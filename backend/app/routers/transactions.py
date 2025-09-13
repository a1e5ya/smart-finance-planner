from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, date
import hashlib

from ..models.database import (
    get_db, Transaction, Account, Category, ImportBatch, AuditLog, 
    CategoryMapping, User, Budget, Goal
)
from ..services.csv_processor import process_csv_upload
from .auth import get_current_user

router = APIRouter()

# Pydantic models
class TransactionResponse(BaseModel):
    id: str
    account_id: Optional[str]
    posted_at: str
    amount: str
    currency: str
    merchant: Optional[str]
    memo: Optional[str]
    category_id: Optional[str]
    category_name: Optional[str]
    category_icon: Optional[str]
    source_category: str
    import_batch_id: Optional[str]
    
    # Enhanced fields
    transaction_type: Optional[str]
    main_category: Optional[str]
    csv_category: Optional[str] 
    csv_subcategory: Optional[str]
    owner: Optional[str]
    is_expense: bool
    is_income: bool
    year: Optional[int]
    month: Optional[int]
    year_month: Optional[str]
    weekday: Optional[str]
    transfer_pair_id: Optional[str]
    confidence_score: Optional[float]
    review_needed: bool
    tags: Optional[List[str]]
    notes: Optional[str]
    created_at: str

class ImportResponse(BaseModel):
    success: bool
    batch_id: str
    summary: Dict[str, Any]
    message: str

class TransactionSummary(BaseModel):
    total_transactions: int
    total_amount: float
    income_amount: float
    expense_amount: float
    transfer_amount: float
    categorized_count: int
    categorization_rate: float
    date_range: Dict[str, Optional[str]]
    by_type: Dict[str, int]
    by_month: Dict[str, float]
    recent_imports: List[Dict[str, Any]]
    top_merchants: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]

class CategoryAssignment(BaseModel):
    category_id: str
    confidence: Optional[float] = 1.0
    notes: Optional[str] = None

class TransactionUpdate(BaseModel):
    merchant: Optional[str] = None
    memo: Optional[str] = None
    amount: Optional[float] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

@router.post("/import", response_model=ImportResponse)
async def import_transactions(
    file: UploadFile = File(...),
    account_name: Optional[str] = Form("Default Account"),
    account_type: Optional[str] = Form("checking"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import transactions from CSV file with enhanced processing"""
    
    print(f"📤 Import request received: {file.filename}")
    print(f"👤 Current user: {current_user.email if current_user else 'None'}")
    
    if not current_user:
        print("❌ No authenticated user for import")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate file
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")
    
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        print(f"📁 Processing file: {file.filename} ({file.size} bytes)")
        
        # Read file content
        file_content = await file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Check for duplicate file uploads
        existing_batch = await db.execute(
            select(ImportBatch).where(
                and_(
                    ImportBatch.user_id == current_user.id,
                    ImportBatch.file_hash == file_hash,
                    ImportBatch.status == "completed"
                )
            )
        )
        
        if existing_batch.scalar_one_or_none():
            return ImportResponse(
                success=False,
                batch_id="",
                summary={"error": "duplicate_file"},
                message="This file has already been imported successfully"
            )
        
        # Create import batch record
        import_batch = ImportBatch(
            user_id=current_user.id,
            filename=file.filename,
            file_size=len(file_content),
            file_hash=file_hash,
            status="processing"
        )
        db.add(import_batch)
        await db.commit()
        await db.refresh(import_batch)
        
        print(f"✅ Created import batch: {import_batch.id}")
        
        # Find or create account
        account = None
        if account_name:
            result = await db.execute(
                select(Account).where(
                    and_(Account.user_id == current_user.id, Account.name == account_name)
                )
            )
            account = result.scalar_one_or_none()
            
            if not account:
                account = Account(
                    user_id=current_user.id,
                    name=account_name,
                    account_type=account_type
                )
                db.add(account)
                await db.commit()
                await db.refresh(account)
                print(f"✅ Created new account: {account.name}")
        
        # Process CSV with enhanced processor
        print("🔄 Processing CSV data...")
        transactions_data, summary = process_csv_upload(
            file_content, 
            file.filename, 
            str(current_user.id),
            str(account.id) if account else None
        )
        
        print(f"📊 CSV processing summary: {summary}")
        
        # Insert transactions with enhanced data
        inserted_count = 0
        duplicate_count = 0
        category_mappings = {}  # Cache for category lookups
        
        # Pre-load user's categories for mapping
        categories_result = await db.execute(
            select(Category).where(Category.user_id == current_user.id)
        )
        user_categories = {cat.name.lower(): cat for cat in categories_result.scalars().all()}
        
        for trans_data in transactions_data:
            # Check for duplicates
            existing = await db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.user_id == current_user.id,
                        Transaction.hash_dedupe == trans_data['hash_dedupe']
                    )
                )
            )
            
            if existing.scalar_one_or_none():
                duplicate_count += 1
                continue
            
            # Try to map category from CSV data
            category_id = None
            confidence_score = None
            
            # Check if we can map the CSV category to our system
            if trans_data.get('csv_category'):
                csv_cat_lower = trans_data['csv_category'].lower()
                if csv_cat_lower in user_categories:
                    category_id = user_categories[csv_cat_lower].id
                    confidence_score = 0.95  # High confidence for exact matches
            
            # Determine if review is needed
            review_needed = (
                category_id is None or  # No category mapping found
                confidence_score is None or confidence_score < 0.8 or  # Low confidence
                not trans_data.get('merchant') or  # Missing merchant
                trans_data.get('amount', 0) == 0  # Zero amount
            )
            
            # Create transaction with all enhanced fields
            transaction = Transaction(
                id=uuid.uuid4(),
                user_id=current_user.id,
                account_id=uuid.UUID(trans_data['account_id']) if trans_data.get('account_id') else None,
                posted_at=trans_data['posted_at'],
                amount=trans_data['amount'],
                currency=trans_data.get('currency', 'USD'),
                merchant=trans_data.get('merchant'),
                memo=trans_data.get('memo'),
                category_id=category_id,
                import_batch_id=import_batch.id,
                hash_dedupe=trans_data['hash_dedupe'],
                source_category=trans_data.get('source_category', 'imported'),
                
                # Enhanced fields from CSV
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
                
                # Analysis fields
                confidence_score=confidence_score,
                review_needed=review_needed,
                tags=None,  # Will be populated by rules later
                notes=None
            )
            
            db.add(transaction)
            inserted_count += 1
        
        # Update import batch with final results
        import_batch.rows_total = len(transactions_data)
        import_batch.rows_imported = inserted_count
        import_batch.rows_duplicated = duplicate_count
        import_batch.rows_errors = summary.get('errors', 0)
        import_batch.status = "completed"
        import_batch.completed_at = datetime.utcnow()
        import_batch.summary_data = summary
        
        await db.commit()
        
        print(f"✅ Import completed: {inserted_count} imported, {duplicate_count} duplicates")
        
        # Log the import activity
        audit_entry = AuditLog(
            user_id=current_user.id,
            firebase_uid=current_user.firebase_uid,
            entity="transaction",
            action="bulk_import",
            details={
                "filename": file.filename,
                "batch_id": str(import_batch.id),
                "rows_imported": inserted_count,
                "rows_duplicated": duplicate_count,
                "summary": summary
            }
        )
        db.add(audit_entry)
        await db.commit()
        
        # Prepare enhanced response
        final_summary = {
            **summary,
            "rows_inserted": inserted_count,
            "rows_duplicated": duplicate_count,
            "batch_id": str(import_batch.id),
            "categories_mapped": len([t for t in transactions_data if t.get('csv_category')]),
            "review_needed": sum(1 for _ in range(inserted_count))  # Will be calculated properly
        }
        
        return ImportResponse(
            success=True,
            batch_id=str(import_batch.id),
            summary=final_summary,
            message=f"Successfully imported {inserted_count} transactions ({duplicate_count} duplicates skipped)"
        )
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        
        # Update import batch with error
        if 'import_batch' in locals():
            import_batch.status = "failed"
            import_batch.error_message = str(e)
            import_batch.completed_at = datetime.utcnow()
            await db.commit()
        
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/list", response_model=List[TransactionResponse])
async def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    merchant: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    review_needed: Optional[bool] = Query(None),
    sort_by: str = Query("posted_at", regex="^(posted_at|amount|merchant|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of transactions with enhanced filters"""
    
    print(f"📋 Transaction list request: page={page}, limit={limit}")
    print(f"👤 Current user: {current_user.email if current_user else 'None'}")
    
    if not current_user:
        print("❌ No authenticated user for transaction list")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Build query with enhanced filters
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    
    # Apply filters
    if start_date:
        query = query.where(Transaction.posted_at >= start_date)
    if end_date:
        query = query.where(Transaction.posted_at <= end_date)
    if min_amount is not None:
        query = query.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Transaction.amount <= max_amount)
    if merchant:
        query = query.where(Transaction.merchant.ilike(f"%{merchant}%"))
    if category_id:
        query = query.where(Transaction.category_id == uuid.UUID(category_id))
    if account_id:
        query = query.where(Transaction.account_id == uuid.UUID(account_id))
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if review_needed is not None:
        query = query.where(Transaction.review_needed == review_needed)
    
    # Add sorting
    sort_column = getattr(Transaction, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Add secondary sort by created_at for consistency
    if sort_by != "created_at":
        query = query.order_by(desc(Transaction.created_at))
    
    # Add pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute query with relationships
    query = query.options(selectinload(Transaction.category))
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    print(f"✅ Found {len(transactions)} transactions")
    
    # Convert to response format with enhanced data
    response_data = []
    for transaction in transactions:
        response_data.append(TransactionResponse(
            id=str(transaction.id),
            account_id=str(transaction.account_id) if transaction.account_id else None,
            posted_at=transaction.posted_at.isoformat(),
            amount=str(transaction.amount),
            currency=transaction.currency,
            merchant=transaction.merchant,
            memo=transaction.memo,
            category_id=str(transaction.category_id) if transaction.category_id else None,
            category_name=transaction.category.name if transaction.category else None,
            category_icon=transaction.category.icon if transaction.category else None,
            source_category=transaction.source_category,
            import_batch_id=str(transaction.import_batch_id) if transaction.import_batch_id else None,
            
            # Enhanced fields
            transaction_type=transaction.transaction_type,
            main_category=transaction.main_category,
            csv_category=transaction.csv_category,
            csv_subcategory=transaction.csv_subcategory,
            owner=transaction.owner,
            is_expense=transaction.is_expense,
            is_income=transaction.is_income,
            year=transaction.year,
            month=transaction.month,
            year_month=transaction.year_month,
            weekday=transaction.weekday,
            transfer_pair_id=transaction.transfer_pair_id,
            confidence_score=float(transaction.confidence_score) if transaction.confidence_score else None,
            review_needed=transaction.review_needed,
            tags=transaction.tags if transaction.tags else [],
            notes=transaction.notes,
            created_at=transaction.created_at.isoformat()
        ))
    
    return response_data

@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive transaction summary with analytics"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    base_query = select(Transaction).where(Transaction.user_id == current_user.id)
    
    # Apply date filters if provided
    if start_date:
        base_query = base_query.where(Transaction.posted_at >= start_date)
    if end_date:
        base_query = base_query.where(Transaction.posted_at <= end_date)
    
    # Get total count and amounts
    count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
    if start_date:
        count_query = count_query.where(Transaction.posted_at >= start_date)
    if end_date:
        count_query = count_query.where(Transaction.posted_at <= end_date)
    
    count_result = await db.execute(count_query)
    total_transactions = count_result.scalar()
    
    # Get amounts by type
    amounts_query = select(
        Transaction.transaction_type,
        func.sum(Transaction.amount).label('total_amount'),
        func.count(Transaction.id).label('count')
    ).where(Transaction.user_id == current_user.id)
    
    if start_date:
        amounts_query = amounts_query.where(Transaction.posted_at >= start_date)
    if end_date:
        amounts_query = amounts_query.where(Transaction.posted_at <= end_date)
    
    amounts_query = amounts_query.group_by(Transaction.transaction_type)
    amounts_result = await db.execute(amounts_query)
    
    by_type = {}
    total_amount = 0
    income_amount = 0
    expense_amount = 0
    transfer_amount = 0
    
    for row in amounts_result:
        trans_type = row.transaction_type or 'unknown'
        amount = float(row.total_amount or 0)
        count = row.count
        
        by_type[trans_type] = count
        total_amount += amount
        
        if trans_type == 'income':
            income_amount = amount
        elif trans_type == 'expense':
            expense_amount = abs(amount)  # Make positive for display
        elif trans_type == 'transfer':
            transfer_amount = amount
    
    # Get date range
    date_query = select(
        func.min(Transaction.posted_at),
        func.max(Transaction.posted_at)
    ).where(Transaction.user_id == current_user.id)
    
    if start_date:
        date_query = date_query.where(Transaction.posted_at >= start_date)
    if end_date:
        date_query = date_query.where(Transaction.posted_at <= end_date)
    
    date_result = await db.execute(date_query)
    min_date, max_date = date_result.first()
    
    # Get categorization stats
    categorized_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.category_id.isnot(None)
        )
    )
    
    if start_date:
        categorized_query = categorized_query.where(Transaction.posted_at >= start_date)
    if end_date:
        categorized_query = categorized_query.where(Transaction.posted_at <= end_date)
    
    categorized_result = await db.execute(categorized_query)
    categorized_count = categorized_result.scalar()
    
    # Get spending by month
    monthly_query = select(
        Transaction.year_month,
        func.sum(Transaction.amount).label('amount')
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense'
        )
    )
    
    if start_date:
        monthly_query = monthly_query.where(Transaction.posted_at >= start_date)
    if end_date:
        monthly_query = monthly_query.where(Transaction.posted_at <= end_date)
    
    monthly_query = monthly_query.group_by(Transaction.year_month).order_by(Transaction.year_month)
    monthly_result = await db.execute(monthly_query)
    
    by_month = {row.year_month: float(abs(row.amount)) for row in monthly_result if row.year_month}
    
    # Get top merchants
    merchants_query = select(
        Transaction.merchant,
        func.count(Transaction.id).label('count'),
        func.sum(func.abs(Transaction.amount)).label('total')
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.merchant.isnot(None),
            Transaction.merchant != ''
        )
    )
    
    if start_date:
        merchants_query = merchants_query.where(Transaction.posted_at >= start_date)
    if end_date:
        merchants_query = merchants_query.where(Transaction.posted_at <= end_date)
    
    merchants_query = merchants_query.group_by(Transaction.merchant).order_by(desc('total')).limit(10)
    merchants_result = await db.execute(merchants_query)
    
    top_merchants = [
        {
            "name": row.merchant,
            "count": row.count,
            "total": float(row.total)
        }
        for row in merchants_result
    ]
    
    # Get top categories
    categories_query = select(
        Category.name,
        Category.icon,
        func.count(Transaction.id).label('count'),
        func.sum(func.abs(Transaction.amount)).label('total')
    ).join(
        Transaction, Transaction.category_id == Category.id
    ).where(
        Transaction.user_id == current_user.id
    )
    
    if start_date:
        categories_query = categories_query.where(Transaction.posted_at >= start_date)
    if end_date:
        categories_query = categories_query.where(Transaction.posted_at <= end_date)
    
    categories_query = categories_query.group_by(Category.id, Category.name, Category.icon).order_by(desc('total')).limit(10)
    categories_result = await db.execute(categories_query)
    
    top_categories = [
        {
            "name": row.name,
            "icon": row.icon,
            "count": row.count,
            "total": float(row.total)
        }
        for row in categories_result
    ]
    
    # Get recent imports
    recent_imports_query = select(ImportBatch).where(
        ImportBatch.user_id == current_user.id
    ).order_by(desc(ImportBatch.created_at)).limit(5)
    recent_imports_result = await db.execute(recent_imports_query)
    recent_imports = recent_imports_result.scalars().all()
    
    return TransactionSummary(
        total_transactions=total_transactions,
        total_amount=total_amount,
        income_amount=income_amount,
        expense_amount=expense_amount,
        transfer_amount=transfer_amount,
        categorized_count=categorized_count,
        categorization_rate=categorized_count / total_transactions if total_transactions > 0 else 0,
        date_range={
            "earliest": min_date.isoformat() if min_date else None,
            "latest": max_date.isoformat() if max_date else None
        },
        by_type=by_type,
        by_month=by_month,
        top_merchants=top_merchants,
        top_categories=top_categories,
        recent_imports=[
            {
                "id": str(batch.id),
                "filename": batch.filename,
                "rows_imported": batch.rows_imported,
                "status": batch.status,
                "created_at": batch.created_at.isoformat()
            }
            for batch in recent_imports
        ]
    )

@router.post("/categorize/{transaction_id}")
async def categorize_transaction(
    transaction_id: str,
    assignment: CategoryAssignment,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually categorize a transaction with confidence tracking"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get transaction
    transaction_query = select(Transaction).where(
        and_(
            Transaction.id == uuid.UUID(transaction_id),
            Transaction.user_id == current_user.id
        )
    )
    result = await db.execute(transaction_query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Verify category belongs to user
    category_query = select(Category).where(
        and_(
            Category.id == uuid.UUID(assignment.category_id),
            Category.user_id == current_user.id
        )
    )
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Store old values for audit
    old_values = {
        "category_id": str(transaction.category_id) if transaction.category_id else None,
        "confidence_score": float(transaction.confidence_score) if transaction.confidence_score else None,
        "source_category": transaction.source_category,
        "notes": transaction.notes
    }
    
    # Update transaction
    transaction.category_id = uuid.UUID(assignment.category_id)
    transaction.source_category = "user"
    transaction.confidence_score = assignment.confidence or 1.0
    transaction.review_needed = False  # User has reviewed it
    transaction.updated_at = datetime.utcnow()
    
    if assignment.notes:
        transaction.notes = assignment.notes
    
    await db.commit()
    
    # Log the categorization
    audit_entry = AuditLog(
        user_id=current_user.id,
        firebase_uid=current_user.firebase_uid,
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
    db.add(audit_entry)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Transaction categorized as {category.name}",
        "category": {
            "id": str(category.id),
            "name": category.name,
            "icon": category.icon
        }
    }

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update transaction details"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get transaction
    transaction_query = select(Transaction).where(
        and_(
            Transaction.id == uuid.UUID(transaction_id),
            Transaction.user_id == current_user.id
        )
    )
    result = await db.execute(transaction_query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
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
    if update_data.merchant is not None:
        transaction.merchant = update_data.merchant
    if update_data.memo is not None:
        transaction.memo = update_data.memo
    if update_data.amount is not None:
        transaction.amount = update_data.amount
    if update_data.category_id is not None:
        # Verify category exists and belongs to user
        category_query = select(Category).where(
            and_(
                Category.id == uuid.UUID(update_data.category_id),
                Category.user_id == current_user.id
            )
        )
        category_result = await db.execute(category_query)
        if not category_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Category not found")
        transaction.category_id = uuid.UUID(update_data.category_id)
    if update_data.tags is not None:
        transaction.tags = update_data.tags
    if update_data.notes is not None:
        transaction.notes = update_data.notes
    
    transaction.updated_at = datetime.utcnow()
    await db.commit()
    
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
        user_id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        entity="transaction",
        entity_id=str(transaction.id),
        action="update",
        before_json=old_values,
        after_json=new_values
    )
    db.add(audit_entry)
    await db.commit()
    
    return {
        "success": True,
        "message": "Transaction updated successfully"
    }

@router.delete("/batch/{batch_id}")
async def delete_import_batch(
    batch_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an import batch and all its transactions"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get import batch
    batch_query = select(ImportBatch).where(
        and_(
            ImportBatch.id == uuid.UUID(batch_id),
            ImportBatch.user_id == current_user.id
        )
    )
    result = await db.execute(batch_query)
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    
    # Get all transactions from this batch
    transactions_query = select(Transaction).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.import_batch_id == uuid.UUID(batch_id)
        )
    )
    transactions_result = await db.execute(transactions_query)
    transactions = transactions_result.scalars().all()
    
    # Delete transactions
    for transaction in transactions:
        await db.delete(transaction)
    
    # Delete the batch
    await db.delete(batch)
    await db.commit()
    
    # Log the deletion
    audit_entry = AuditLog(
        user_id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        entity="import_batch",
        entity_id=str(batch.id),
        action="delete",
        details={
            "filename": batch.filename,
            "transactions_deleted": len(transactions)
        }
    )
    db.add(audit_entry)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Deleted {len(transactions)} transactions from batch {batch.filename}"
    }

@router.get("/review")
async def get_transactions_needing_review(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get transactions that need manual review"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Query transactions needing review
    query = select(Transaction).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.review_needed == True
        )
    ).order_by(desc(Transaction.posted_at))
    
    # Add pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute with category relationship
    query = query.options(selectinload(Transaction.category))
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Get total count for pagination
    count_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.review_needed == True
        )
    )
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()
    
    # Convert to response format
    response_data = []
    for transaction in transactions:
        response_data.append({
            "id": str(transaction.id),
            "posted_at": transaction.posted_at.isoformat(),
            "amount": str(transaction.amount),
            "merchant": transaction.merchant,
            "memo": transaction.memo,
            "transaction_type": transaction.transaction_type,
            "csv_category": transaction.csv_category,
            "csv_subcategory": transaction.csv_subcategory,
            "main_category": transaction.main_category,
            "confidence_score": float(transaction.confidence_score) if transaction.confidence_score else None,
            "suggested_categories": []  # Could be populated by ML later
        })
    
    return {
        "transactions": response_data,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "has_more": len(response_data) == limit
    }

@router.post("/bulk-categorize")
async def bulk_categorize_transactions(
    transaction_ids: List[str],
    category_id: str,
    confidence: float = 1.0,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk categorize multiple transactions"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not transaction_ids:
        raise HTTPException(status_code=400, detail="No transaction IDs provided")
    
    # Verify category exists and belongs to user
    category_query = select(Category).where(
        and_(
            Category.id == uuid.UUID(category_id),
            Category.user_id == current_user.id
        )
    )
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get transactions
    transaction_uuids = [uuid.UUID(tid) for tid in transaction_ids]
    transactions_query = select(Transaction).where(
        and_(
            Transaction.id.in_(transaction_uuids),
            Transaction.user_id == current_user.id
        )
    )
    result = await db.execute(transactions_query)
    transactions = result.scalars().all()
    
    if len(transactions) != len(transaction_ids):
        raise HTTPException(status_code=404, detail="Some transactions not found")
    
    # Update all transactions
    updated_count = 0
    for transaction in transactions:
        old_category_id = transaction.category_id
        transaction.category_id = uuid.UUID(category_id)
        transaction.source_category = "user"
        transaction.confidence_score = confidence
        transaction.review_needed = False
        transaction.updated_at = datetime.utcnow()
        updated_count += 1
    
    await db.commit()
    
    # Log bulk operation
    audit_entry = AuditLog(
        user_id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        entity="transaction",
        action="bulk_categorize",
        details={
            "category_id": category_id,
            "category_name": category.name,
            "transaction_count": updated_count,
            "transaction_ids": transaction_ids
        }
    )
    db.add(audit_entry)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Successfully categorized {updated_count} transactions as {category.name}",
        "updated_count": updated_count
    }

@router.get("/analytics/spending-trends")
async def get_spending_trends(
    months: int = Query(12, ge=1, le=24),
    category_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get spending trends over time"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Base query for expenses
    query = select(
        Transaction.year_month,
        func.sum(func.abs(Transaction.amount)).label('total_amount'),
        func.count(Transaction.id).label('transaction_count')
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense'
        )
    )
    
    # Add category filter if specified
    if category_id:
        query = query.where(Transaction.category_id == uuid.UUID(category_id))
    
    # Group by month and order
    query = query.group_by(Transaction.year_month).order_by(Transaction.year_month.desc()).limit(months)
    
    result = await db.execute(query)
    trends = []
    
    for row in result:
        if row.year_month:
            trends.append({
                "month": row.year_month,
                "amount": float(row.total_amount),
                "transaction_count": row.transaction_count
            })
    
    # Reverse to get chronological order
    trends.reverse()
    
    return {
        "trends": trends,
        "months": len(trends),
        "category_filter": category_id
    }

@router.get("/analytics/merchant-analysis")
async def get_merchant_analysis(
    limit: int = Query(20, ge=5, le=100),
    min_transactions: int = Query(2, ge=1),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze spending patterns by merchant"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    query = select(
        Transaction.merchant,
        func.count(Transaction.id).label('transaction_count'),
        func.sum(func.abs(Transaction.amount)).label('total_amount'),
        func.avg(func.abs(Transaction.amount)).label('avg_amount'),
        func.min(Transaction.posted_at).label('first_transaction'),
        func.max(Transaction.posted_at).label('last_transaction')
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.merchant.isnot(None),
            Transaction.merchant != ''
        )
    ).group_by(Transaction.merchant).having(
        func.count(Transaction.id) >= min_transactions
    ).order_by(desc('total_amount')).limit(limit)
    
    result = await db.execute(query)
    merchants = []
    
    for row in result:
        # Calculate frequency (transactions per month)
        days_span = (row.last_transaction - row.first_transaction).days
        months_span = max(1, days_span / 30.44)  # Average days per month
        frequency = row.transaction_count / months_span
        
        merchants.append({
            "merchant": row.merchant,
            "transaction_count": row.transaction_count,
            "total_amount": float(row.total_amount),
            "average_amount": float(row.avg_amount),
            "frequency_per_month": round(frequency, 2),
            "first_transaction": row.first_transaction.isoformat(),
            "last_transaction": row.last_transaction.isoformat()
        })
    
    return {
        "merchants": merchants,
        "analysis_criteria": {
            "min_transactions": min_transactions,
            "limit": limit
        }
    }