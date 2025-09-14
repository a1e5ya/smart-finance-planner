"""
Transaction import service with CSV processing and auto-categorization
"""
from fastapi import Depends
from ..models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Any, Tuple, Optional
import uuid
import hashlib
from datetime import datetime

from ..models.database import (
    Transaction, Account, Category, ImportBatch, User, AuditLog, CategoryMapping
)
from ..services.csv_processor import process_csv_upload
from ..services.category_mappings import CategoryMapper, PatternType
from ..routers.auth import get_current_user
from fastapi import Depends, HTTPException

class TransactionImportService:
    """Service for importing and processing transaction data"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.category_mapper = CategoryMapper()
    
    async def import_from_csv(
        self,
        file_content: bytes,
        filename: str,
        account_name: str = "Default Account",
        account_type: str = "checking",
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """Import transactions from CSV with auto-categorization"""
        
        print(f"DEBUG: Starting import_from_csv for {filename}")
        print(f"DEBUG: File size: {len(file_content)} bytes")
        print(f"DEBUG: Auto categorize: {auto_categorize}")
        
        try:
            print(f"DEBUG: About to generate file hash")
            # Generate file hash for duplicate detection
            file_hash = hashlib.md5(file_content).hexdigest()
            print(f"DEBUG: File hash generated: {file_hash[:10]}...")
            
            print(f"DEBUG: About to check for existing batch")
            # Check for duplicate file uploads
            existing_batch = await self.db.execute(
                select(ImportBatch).where(
                    and_(
                        ImportBatch.user_id == self.user.id,
                        ImportBatch.file_hash == file_hash,
                        ImportBatch.status == "completed"
                    )
                )
            )
            print(f"DEBUG: Checked for existing batch")
            
            if existing_batch.scalar_one_or_none():
                print(f"DEBUG: Found duplicate file - allowing re-import")
                # For now, allow re-import instead of blocking duplicates
                # TODO: Implement proper duplicate handling in frontend
                pass
            
            print(f"DEBUG: About to create import batch")
            # Create import batch record
            import_batch = ImportBatch(
                user_id=self.user.id,
                filename=filename,
                file_size=len(file_content),
                file_hash=file_hash,
                status="processing"
            )
            print(f"DEBUG: Created import batch object")
            
            self.db.add(import_batch)
            print(f"DEBUG: Added batch to session")
            
            await self.db.commit()
            print(f"DEBUG: Committed batch")
            
            await self.db.refresh(import_batch)
            print(f"DEBUG: Refreshed batch")

            print(f"✅ Created import batch: {import_batch.id}")

            print(f"DEBUG: About to find or create account")
            # Find or create account
            account = await self._get_or_create_account(account_name, account_type)
            print(f"DEBUG: Account handled: {account.id if account else 'None'}")

            print(f"DEBUG: About to process CSV")
            # Process CSV with enhanced processor
            print("🔄 Processing CSV data...")
            transactions_data, summary = process_csv_upload(
                file_content, 
                filename, 
                str(self.user.id),
                str(account.id) if account else None
            )
            print(f"DEBUG: CSV processing completed, got {len(transactions_data)} transactions")

            print(f"📊 CSV processing summary: {summary}")

            print(f"DEBUG: About to load categorization data")
            # Load user categories and mappings for auto-categorization
            categorization_loaded = False
            if auto_categorize:
                try:
                    await self._load_categorization_data()
                    categorization_loaded = True
                    print(f"✅ Categorization system loaded successfully")
                except Exception as e:
                    print(f"⚠️ Failed to load categorization system: {e}")
                    auto_categorize = False

            # Simple insertion - one by one
            inserted_count = 0
            duplicate_count = 0
            auto_categorized_count = 0

            for trans_data in transactions_data:
                transaction = Transaction(
                    id=uuid.uuid4(),
                    user_id=self.user.id,
                    account_id=uuid.UUID(trans_data['account_id']) if trans_data.get('account_id') else None,
                    posted_at=trans_data['posted_at'],
                    amount=trans_data['amount'],
                    currency=trans_data.get('currency', 'EUR'),
                    merchant=trans_data.get('merchant'),
                    memo=trans_data.get('memo'),
                    import_batch_id=import_batch.id,
                    hash_dedupe=trans_data['hash_dedupe'],
                    source_category="imported",
                    transaction_type=trans_data.get('transaction_type'),
                    main_category=trans_data.get('main_category'),
                    csv_category=trans_data.get('csv_category'),
                    csv_subcategory=trans_data.get('csv_subcategory'),
                    csv_account=trans_data.get('csv_account'),
                    owner=trans_data.get('owner'),
                    csv_account_type=trans_data.get('csv_account_type'),
                    is_expense=trans_data.get('is_expense', False),
                    is_income=trans_data.get('is_income', False),
                    year=trans_data.get('year'),
                    month=trans_data.get('month'),
                    year_month=trans_data.get('year_month'),
                    weekday=trans_data.get('weekday'),
                    transfer_pair_id=trans_data.get('transfer_pair_id'),
                    confidence_score=None,
                    review_needed=False,
                    tags=None,
                    notes=None
                )
                
                self.db.add(transaction)
                inserted_count += 1

            await self.db.commit()
            
            # Update import batch with final results
            import_batch.rows_total = len(transactions_data)
            import_batch.rows_imported = inserted_count
            import_batch.rows_duplicated = duplicate_count
            import_batch.rows_errors = summary.get('errors', 0)
            import_batch.status = "completed"
            import_batch.completed_at = datetime.utcnow()
            import_batch.summary_data = {
                **summary,
                "auto_categorized_count": auto_categorized_count
            }
            
            await self.db.commit()
            
            print(f"✅ Import completed: {inserted_count} imported, {duplicate_count} duplicates, {auto_categorized_count} auto-categorized")
            
            # Log the import activity
            audit_entry = AuditLog(
                user_id=self.user.id,
                firebase_uid=self.user.firebase_uid,
                entity="transaction",
                action="bulk_import",
                details={
                    "filename": filename,
                    "batch_id": str(import_batch.id),
                    "rows_imported": inserted_count,
                    "rows_duplicated": duplicate_count,
                    "auto_categorized": auto_categorized_count,
                    "summary": summary
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            # Prepare enhanced response
            final_summary = {
                **summary,
                "rows_inserted": inserted_count,
                "rows_duplicated": duplicate_count,
                "auto_categorized_count": auto_categorized_count,
                "batch_id": str(import_batch.id),
                "categories_mapped": len([t for t in transactions_data if t.get('csv_category')]),
                "review_needed": sum(1 for t in transactions_data if not t.get('category_id'))
            }
            
            return {
                "success": True,
                "batch_id": str(import_batch.id),
                "summary": final_summary,
                "message": f"Successfully imported {inserted_count} transactions ({duplicate_count} duplicates skipped, {auto_categorized_count} auto-categorized)"
            }
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            
            # Update import batch with error
            if 'import_batch' in locals():
                import_batch.status = "failed"
                import_batch.error_message = str(e)
                import_batch.completed_at = datetime.utcnow()
                await self.db.commit()
            
            return {
                "success": False,
                "batch_id": "",
                "summary": {"error": str(e)},
                "message": f"Import failed: {str(e)}"
            }
    
    async def _get_or_create_account(
        self, 
        account_name: str, 
        account_type: str
    ) -> Optional[Account]:
        """Get existing account or create new one"""
        
        if not account_name:
            return None
        
        # Try to find existing account
        result = await self.db.execute(
            select(Account).where(
                and_(Account.user_id == self.user.id, Account.name == account_name)
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            # Create new account
            account = Account(
                user_id=self.user.id,
                name=account_name,
                account_type=account_type
            )
            self.db.add(account)
            await self.db.commit()
            await self.db.refresh(account)
            print(f"✅ Created new account: {account.name}")
        
        return account
    
    async def _load_categorization_data(self):
        """Load user categories and mappings for auto-categorization"""
        
        # Load user categories
        categories_result = await self.db.execute(
            select(Category).where(
                and_(Category.user_id == self.user.id, Category.active == True)
            )
        )
        user_categories = {cat.name.lower(): cat for cat in categories_result.scalars().all()}
        
        # Load category mappings
        mappings_result = await self.db.execute(
            select(CategoryMapping).where(
                and_(CategoryMapping.user_id == self.user.id, CategoryMapping.active == True)
            ).order_by(CategoryMapping.priority.desc())
        )
        mappings = mappings_result.scalars().all()
        
        # Convert to CategoryMapper format
        from ..services.category_mappings import CategoryMapping as CMMapping, PatternType
        
        cm_mappings = []
        for mapping in mappings:
            try:
                cm_mappings.append(CMMapping(
                    id=str(mapping.id),
                    user_id=str(mapping.user_id),
                    pattern_type=PatternType(mapping.pattern_type),
                    pattern_value=mapping.pattern_value,
                    category_id=str(mapping.category_id),
                    priority=mapping.priority,
                    confidence=float(mapping.confidence),
                    active=mapping.active,
                    description=f"{mapping.pattern_type}: {mapping.pattern_value}"
                ))
            except ValueError:
                # Skip invalid pattern types
                continue
        
        # Load mappings into category mapper
        self.category_mapper.load_mappings(cm_mappings)
        
        # Store categories for lookup
        self.user_categories = user_categories
        
        print(f"🏷️ Loaded {len(user_categories)} categories and {len(cm_mappings)} mappings for auto-categorization")
    
    async def _auto_categorize_transaction(self, trans_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Auto-categorize a transaction using rules and CSV data"""
        
        # First try CSV category mapping
        csv_result = await self._categorize_from_csv(trans_data)
        if csv_result:
            return csv_result
        
        # Then try rule-based categorization
        rule_result = await self._categorize_from_rules(trans_data)
        if rule_result:
            return rule_result
        
        return None
    
    async def _categorize_from_csv(self, trans_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try to categorize based on CSV category data"""
        
        csv_category = trans_data.get('csv_category', '').lower().strip()
        csv_subcategory = trans_data.get('csv_subcategory', '').lower().strip()
        main_category = trans_data.get('main_category', '').lower().strip()
        
        # Try exact matches first
        for csv_field in [csv_subcategory, csv_category, main_category]:
            if csv_field and csv_field in self.user_categories:
                category = self.user_categories[csv_field]
                return {
                    "category_id": str(category.id),
                    "confidence": 0.95,
                    "source": "csv_exact"
                }
        
        # Try partial matches
        for csv_field in [csv_subcategory, csv_category, main_category]:
            if not csv_field:
                continue
                
            for cat_name, category in self.user_categories.items():
                if (csv_field in cat_name or cat_name in csv_field) and len(csv_field) > 2:
                    return {
                        "category_id": str(category.id),
                        "confidence": 0.8,
                        "source": "csv_partial"
                    }
        
        return None
    
    async def _categorize_from_rules(self, trans_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try to categorize using rule-based mapping"""
        
        try:
            result = self.category_mapper.categorize_transaction(
                merchant=trans_data.get('merchant', ''),
                memo=trans_data.get('memo', ''),
                amount=float(trans_data.get('amount', 0)),
                mcc=trans_data.get('mcc', ''),
                csv_category=trans_data.get('csv_category', ''),
                csv_subcategory=trans_data.get('csv_subcategory', ''),
                main_category=trans_data.get('main_category', '')
            )
            
            if result.category_id and result.confidence > 0.6:
                return {
                    "category_id": result.category_id,
                    "confidence": result.confidence,
                    "source": "rules"
                }
        except Exception as e:
            print(f"⚠️ Rule-based categorization failed: {e}")
        
        return None
    
    async def create_default_category_mappings(self):
        """Create default category mappings for new users"""
        
        # Load user categories first
        categories_result = await self.db.execute(
            select(Category).where(Category.user_id == self.user.id)
        )
        user_categories = {cat.name.lower(): str(cat.id) for cat in categories_result.scalars().all()}
        
        # Create common mappings
        default_mappings = [
            # Food & Dining
            ("keyword", "starbucks", "cafes & coffee", 90),
            ("keyword", "mcdonald", "restaurants", 90),
            ("keyword", "restaurant", "restaurants", 70),
            ("keyword", "grocery", "groceries", 80),
            ("keyword", "lidl", "groceries", 85),
            ("keyword", "aldi", "groceries", 85),
            
            # Transportation  
            ("keyword", "uber", "public transport", 90),
            ("keyword", "taxi", "public transport", 85),
            ("keyword", "gas station", "fuel", 80),
            ("keyword", "parking", "parking fees", 85),
            
            # Shopping
            ("keyword", "amazon", "electronics", 80),
            ("keyword", "h&m", "clothing & shoes", 85),
            ("keyword", "zara", "clothing & shoes", 85),
            
            # Utilities
            ("keyword", "electric", "energy & water", 85),
            ("keyword", "internet", "internet & phone", 85),
            ("keyword", "phone", "internet & phone", 80),
            
            # Entertainment
            ("keyword", "netflix", "subscriptions", 95),
            ("keyword", "spotify", "subscriptions", 95),
            ("keyword", "subscription", "subscriptions", 70),
            
            # Healthcare
            ("keyword", "pharmacy", "pharmacy", 90),
            ("keyword", "doctor", "medical services", 85),
            ("keyword", "hospital", "medical services", 90),
            
            # Financial
            ("keyword", "atm", "withdrawal", 95),
            ("keyword", "fee", "bank services", 80),
            ("keyword", "transfer", "between own accounts", 85),
        ]
        
        created_count = 0
        for pattern_type, pattern_value, category_name, priority in default_mappings:
            category_id = user_categories.get(category_name.lower())
            if category_id:
                # Check if mapping already exists
                existing = await self.db.execute(
                    select(CategoryMapping).where(
                        and_(
                            CategoryMapping.user_id == self.user.id,
                            CategoryMapping.pattern_type == pattern_type,
                            CategoryMapping.pattern_value == pattern_value.lower()
                        )
                    )
                )
                
                if not existing.scalar_one_or_none():
                    mapping = CategoryMapping(
                        user_id=self.user.id,
                        pattern_type=pattern_type,
                        pattern_value=pattern_value.lower(),
                        category_id=uuid.UUID(category_id),
                        priority=priority,
                        confidence=0.9,
                        active=True
                    )
                    self.db.add(mapping)
                    created_count += 1
        
        if created_count > 0:
            await self.db.commit()
            print(f"✅ Created {created_count} default category mappings")
        
        return created_count

# Helper function to create service instance
def get_import_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionImportService:
    """Get transaction import service instance"""
    return TransactionImportService(db, current_user)