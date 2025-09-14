"""
Transaction service - Business logic for transaction operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from ..models.database import Transaction, Category, User, AuditLog, ImportBatch, get_db
from ..routers.auth import get_current_user
from fastapi import Depends, HTTPException

class TransactionService:
    """Service for transaction operations"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def delete_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Delete a single transaction"""
        try:
            # Get transaction first to verify ownership and get details for audit
            transaction_query = select(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(transaction_query)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return {
                    "success": False,
                    "message": "Transaction not found",
                    "deleted_count": 0
                }
            
            # Store transaction details for audit log
            transaction_details = {
                "id": str(transaction.id),
                "posted_at": transaction.posted_at.isoformat(),
                "amount": str(transaction.amount),
                "merchant": transaction.merchant,
                "memo": transaction.memo,
                "category_id": str(transaction.category_id) if transaction.category_id else None,
                "import_batch_id": str(transaction.import_batch_id) if transaction.import_batch_id else None
            }
            
            # Delete the transaction
            delete_query = delete(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            await self.db.execute(delete_query)
            await self.db.commit()
            
            # Log the deletion
            audit_entry = AuditLog(
                user_id=self.user.id,
                firebase_uid=self.user.firebase_uid,
                entity="transaction",
                entity_id=transaction_id,
                action="delete",
                before_json=transaction_details,
                after_json=None,
                details={"reason": "user_requested"}
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Transaction deleted: {transaction_id}")
            
            return {
                "success": True,
                "message": f"Transaction deleted successfully",
                "deleted_count": 1
            }
            
        except Exception as e:
            print(f"❌ Failed to delete transaction {transaction_id}: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to delete transaction: {str(e)}",
                "deleted_count": 0
            }
    
    async def categorize_transaction(
        self, 
        transaction_id: str, 
        category_id: str,
        confidence: float = 1.0,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Categorize a single transaction with proper error handling"""
        try:
            # Get transaction with user verification
            transaction_query = select(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(transaction_query)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return {
                    "success": False,
                    "message": "Transaction not found"
                }
            
            # Verify category belongs to user
            category_query = select(Category).where(
                and_(
                    Category.id == uuid.UUID(category_id),
                    Category.user_id == self.user.id
                )
            )
            category_result = await self.db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category:
                return {
                    "success": False,
                    "message": "Category not found or access denied"
                }
            
            # Store old values for audit
            old_values = {
                "category_id": str(transaction.category_id) if transaction.category_id else None,
                "confidence_score": float(transaction.confidence_score) if transaction.confidence_score else None,
                "source_category": transaction.source_category,
                "notes": transaction.notes
            }
            
            # Update transaction
            transaction.category_id = uuid.UUID(category_id)
            transaction.source_category = "user"
            transaction.confidence_score = confidence
            transaction.review_needed = False
            transaction.updated_at = datetime.utcnow()
            
            if notes:
                transaction.notes = notes
            
            await self.db.commit()
            
            # Log the categorization
            audit_entry = AuditLog(
                user_id=self.user.id,
                firebase_uid=self.user.firebase_uid,
                entity="transaction",
                entity_id=str(transaction.id),
                action="categorize",
                before_json=old_values,
                after_json={
                    "category_id": str(transaction.category_id),
                    "category_name": category.name,
                    "confidence_score": float(transaction.confidence_score),
                    "source_category": transaction.source_category,
                    "notes": transaction.notes
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Transaction categorized: {transaction_id} -> {category.name}")
            
            return {
                "success": True,
                "message": f"Transaction categorized as {category.name}",
                "category": {
                    "id": str(category.id),
                    "name": category.name,
                    "icon": category.icon
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to categorize transaction {transaction_id}: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to categorize transaction: {str(e)}"
            }
    
    async def bulk_categorize_transactions(
        self,
        transaction_ids: List[str],
        category_id: str,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Bulk categorize multiple transactions"""
        try:
            if not transaction_ids:
                return {
                    "success": False,
                    "message": "No transaction IDs provided",
                    "updated_count": 0
                }
            
            # Verify category exists and belongs to user
            category_query = select(Category).where(
                and_(
                    Category.id == uuid.UUID(category_id),
                    Category.user_id == self.user.id
                )
            )
            category_result = await self.db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category:
                return {
                    "success": False,
                    "message": "Category not found or access denied",
                    "updated_count": 0
                }
            
            # Get transactions
            transaction_uuids = [uuid.UUID(tid) for tid in transaction_ids]
            transactions_query = select(Transaction).where(
                and_(
                    Transaction.id.in_(transaction_uuids),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(transactions_query)
            transactions = result.scalars().all()
            
            if len(transactions) != len(transaction_ids):
                return {
                    "success": False,
                    "message": "Some transactions not found or access denied",
                    "updated_count": 0
                }
            
            # Update all transactions
            updated_count = 0
            for transaction in transactions:
                transaction.category_id = uuid.UUID(category_id)
                transaction.source_category = "user"
                transaction.confidence_score = confidence
                transaction.review_needed = False
                transaction.updated_at = datetime.utcnow()
                updated_count += 1
            
            await self.db.commit()
            
            # Log bulk operation
            audit_entry = AuditLog(
                user_id=self.user.id,
                firebase_uid=self.user.firebase_uid,
                entity="transaction",
                action="bulk_categorize",
                details={
                    "category_id": category_id,
                    "category_name": category.name,
                    "transaction_count": updated_count,
                    "transaction_ids": transaction_ids
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Bulk categorized {updated_count} transactions as {category.name}")
            
            return {
                "success": True,
                "message": f"Successfully categorized {updated_count} transactions as {category.name}",
                "updated_count": updated_count
            }
            
        except Exception as e:
            print(f"❌ Bulk categorization failed: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Bulk categorization failed: {str(e)}",
                "updated_count": 0
            }
    
    async def update_transaction(
        self,
        transaction_id: str,
        merchant: Optional[str] = None,
        memo: Optional[str] = None,
        amount: Optional[float] = None,
        category_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update transaction details"""
        try:
            # Get transaction
            transaction_query = select(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(transaction_query)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return {
                    "success": False,
                    "message": "Transaction not found"
                }
            
            # Store old values for audit
            old_values = {
                "merchant": transaction.merchant,
                "memo": transaction.memo,
                "amount": float(transaction.amount),
                "category_id": str(transaction.category_id) if transaction.category_id else None,
                "tags": transaction.tags,
                "notes": transaction.notes
            }
            
            # Apply updates
            if merchant is not None:
                transaction.merchant = merchant
            if memo is not None:
                transaction.memo = memo
            if amount is not None:
                transaction.amount = amount
            if category_id is not None:
                # Verify category exists and belongs to user
                category_query = select(Category).where(
                    and_(
                        Category.id == uuid.UUID(category_id),
                        Category.user_id == self.user.id
                    )
                )
                category_result = await self.db.execute(category_query)
                if not category_result.scalar_one_or_none():
                    return {
                        "success": False,
                        "message": "Category not found"
                    }
                transaction.category_id = uuid.UUID(category_id)
            if tags is not None:
                transaction.tags = tags
            if notes is not None:
                transaction.notes = notes
            
            transaction.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # Log the update
            new_values = {
                "merchant": transaction.merchant,
                "memo": transaction.memo,
                "amount": float(transaction.amount),
                "category_id": str(transaction.category_id) if transaction.category_id else None,
                "tags": transaction.tags,
                "notes": transaction.notes
            }
            
            audit_entry = AuditLog(
                user_id=self.user.id,
                firebase_uid=self.user.firebase_uid,
                entity="transaction",
                entity_id=str(transaction.id),
                action="update",
                before_json=old_values,
                after_json=new_values
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Transaction updated: {transaction_id}")
            
            return {
                "success": True,
                "message": "Transaction updated successfully"
            }
            
        except Exception as e:
            print(f"❌ Failed to update transaction {transaction_id}: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to update transaction: {str(e)}"
            }
    
    async def delete_import_batch(self, batch_id: str) -> Dict[str, Any]:
        """Delete an import batch and all its transactions"""
        try:
            # Get import batch
            batch_query = select(ImportBatch).where(
                and_(
                    ImportBatch.id == uuid.UUID(batch_id),
                    ImportBatch.user_id == self.user.id
                )
            )
            result = await self.db.execute(batch_query)
            batch = result.scalar_one_or_none()
            
            if not batch:
                return {
                    "success": False,
                    "message": "Import batch not found",
                    "deleted_count": 0
                }
            
            # Get all transactions from this batch
            transactions_query = select(Transaction).where(
                and_(
                    Transaction.user_id == self.user.id,
                    Transaction.import_batch_id == uuid.UUID(batch_id)
                )
            )
            transactions_result = await self.db.execute(transactions_query)
            transactions = transactions_result.scalars().all()
            
            # Delete transactions
            transaction_count = len(transactions)
            for transaction in transactions:
                await self.db.delete(transaction)
            
            # Delete the batch
            await self.db.delete(batch)
            await self.db.commit()
            
            # Log the deletion
            audit_entry = AuditLog(
                user_id=self.user.id,
                firebase_uid=self.user.firebase_uid,
                entity="import_batch",
                entity_id=str(batch.id),
                action="delete",
                details={
                    "filename": batch.filename,
                    "transactions_deleted": transaction_count
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Deleted batch {batch.filename} with {transaction_count} transactions")
            
            return {
                "success": True,
                "message": f"Deleted {transaction_count} transactions from batch {batch.filename}",
                "deleted_count": transaction_count
            }
            
        except Exception as e:
            print(f"❌ Failed to delete batch {batch_id}: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to delete batch: {str(e)}",
                "deleted_count": 0
            }
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get a single transaction by ID"""
        try:
            query = select(Transaction).options(selectinload(Transaction.category)).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"❌ Failed to get transaction {transaction_id}: {e}")
            return None
    
    async def get_transactions_by_batch(self, batch_id: str) -> List[Transaction]:
        """Get all transactions from a specific import batch"""
        try:
            query = select(Transaction).where(
                and_(
                    Transaction.user_id == self.user.id,
                    Transaction.import_batch_id == uuid.UUID(batch_id)
                )
            ).order_by(Transaction.posted_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"❌ Failed to get transactions for batch {batch_id}: {e}")
            return []
    
    async def recategorize_by_rules(
        self, 
        transaction_ids: Optional[List[str]] = None,
        category_mappings: Optional[List] = None
    ) -> Dict[str, Any]:
        """Recategorize transactions using updated rules"""
        try:
            # If no specific transactions provided, get all uncategorized
            if not transaction_ids:
                query = select(Transaction.id).where(
                    and_(
                        Transaction.user_id == self.user.id,
                        or_(
                            Transaction.category_id.is_(None),
                            Transaction.source_category == 'imported'
                        )
                    )
                )
                result = await self.db.execute(query)
                transaction_ids = [str(row[0]) for row in result]
            
            if not transaction_ids:
                return {
                    "success": True,
                    "message": "No transactions to recategorize",
                    "updated_count": 0
                }
            
            # Load categorization engine if mappings provided
            if category_mappings:
                from ..services.category_mappings import CategoryMapper
                mapper = CategoryMapper()
                mapper.load_mappings(category_mappings)
            
            updated_count = 0
            for tid in transaction_ids:
                transaction = await self.get_transaction_by_id(tid)
                if not transaction:
                    continue
                
                # Try to categorize using rules
                if category_mappings and mapper:
                    result = mapper.categorize_transaction(
                        merchant=transaction.merchant or '',
                        memo=transaction.memo or '',
                        amount=float(transaction.amount),
                        csv_category=transaction.csv_category or '',
                        csv_subcategory=transaction.csv_subcategory or '',
                        main_category=transaction.main_category or ''
                    )
                    
                    if result.category_id and result.confidence > 0.7:
                        transaction.category_id = uuid.UUID(result.category_id)
                        transaction.source_category = "rules"
                        transaction.confidence_score = result.confidence
                        transaction.review_needed = result.confidence < 0.8
                        transaction.updated_at = datetime.utcnow()
                        updated_count += 1
            
            await self.db.commit()
            
            # Log bulk recategorization
            audit_entry = AuditLog(
                user_id=self.user.id,
                firebase_uid=self.user.firebase_uid,
                entity="transaction",
                action="bulk_recategorize",
                details={
                    "transaction_count": len(transaction_ids),
                    "updated_count": updated_count,
                    "method": "rules_based"
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Recategorized {updated_count} of {len(transaction_ids)} transactions")
            
            return {
                "success": True,
                "message": f"Recategorized {updated_count} transactions using rules",
                "updated_count": updated_count,
                "total_processed": len(transaction_ids)
            }
            
        except Exception as e:
            print(f"❌ Bulk recategorization failed: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Recategorization failed: {str(e)}",
                "updated_count": 0
            }
    
    async def get_transaction_statistics(self) -> Dict[str, Any]:
        """Get comprehensive transaction statistics for the user"""
        try:
            # Basic counts
            total_query = select(func.count(Transaction.id)).where(Transaction.user_id == self.user.id)
            total_result = await self.db.execute(total_query)
            total_transactions = total_result.scalar()
            
            # Categorized count
            categorized_query = select(func.count(Transaction.id)).where(
                and_(Transaction.user_id == self.user.id, Transaction.category_id.isnot(None))
            )
            categorized_result = await self.db.execute(categorized_query)
            categorized_count = categorized_result.scalar()
            
            # Review needed count
            review_query = select(func.count(Transaction.id)).where(
                and_(Transaction.user_id == self.user.id, Transaction.review_needed == True)
            )
            review_result = await self.db.execute(review_query)
            review_needed = review_result.scalar()
            
            # By source category
            source_query = select(
                Transaction.source_category,
                func.count(Transaction.id).label('count')
            ).where(Transaction.user_id == self.user.id).group_by(Transaction.source_category)
            
            source_result = await self.db.execute(source_query)
            by_source = {row.source_category: row.count for row in source_result}
            
            # Date range
            date_query = select(
                func.min(Transaction.posted_at),
                func.max(Transaction.posted_at)
            ).where(Transaction.user_id == self.user.id)
            
            date_result = await self.db.execute(date_query)
            min_date, max_date = date_result.first()
            
            return {
                "total_transactions": total_transactions,
                "categorized_count": categorized_count,
                "review_needed": review_needed,
                "categorization_rate": (categorized_count / total_transactions * 100) if total_transactions > 0 else 0,
                "by_source": by_source,
                "date_range": {
                    "earliest": min_date.isoformat() if min_date else None,
                    "latest": max_date.isoformat() if max_date else None
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get transaction statistics: {e}")
            return {
                "total_transactions": 0,
                "categorized_count": 0,
                "review_needed": 0,
                "categorization_rate": 0,
                "by_source": {},
                "date_range": {"earliest": None, "latest": None}
            }

# Helper function to create service instance
def get_transaction_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionService:
    """Get transaction service instance"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return TransactionService(db, current_user)