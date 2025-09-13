from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime, date
import io

from ..models.database import get_db, Transaction, Account, Category, ImportBatch, AuditLog
from ..services.csv_processor import process_csv_upload
from .auth import get_current_user  # Use the same auth function
from ..models.database import User

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
    source_category: str
    import_batch_id: Optional[str]
    created_at: str

class ImportResponse(BaseModel):
    success: bool
    batch_id: str
    summary: dict
    message: str

class TransactionFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    merchant: Optional[str] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None

@router.post("/import", response_model=ImportResponse)
async def import_transactions(
    file: UploadFile = File(...),
    account_name: Optional[str] = Form(None),
    account_type: Optional[str] = Form("checking"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import transactions from CSV file"""
    
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
        
        # Create import batch record
        import_batch = ImportBatch(
            user_id=current_user.id,
            filename=file.filename,
            file_size=len(file_content),
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
        
        # Process CSV
        print("🔄 Processing CSV data...")
        transactions_data, summary = process_csv_upload(
            file_content, 
            file.filename, 
            str(current_user.id),
            str(account.id) if account else None
        )
        
        print(f"📊 CSV processing summary: {summary}")
        
        # Insert transactions
        inserted_count = 0
        duplicate_count = 0
        
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
            
            # Create transaction
            transaction = Transaction(
                id=uuid.uuid4(),
                user_id=current_user.id,
                account_id=uuid.UUID(trans_data['account_id']) if trans_data.get('account_id') else None,
                posted_at=trans_data['posted_at'],
                amount=trans_data['amount'],
                currency=trans_data['currency'],
                merchant=trans_data['merchant'],
                memo=trans_data['memo'],
                import_batch_id=import_batch.id,
                hash_dedupe=trans_data['hash_dedupe'],
                source_category=trans_data['source_category']
            )
            
            db.add(transaction)
            inserted_count += 1
        
        # Update import batch
        import_batch.rows_imported = inserted_count
        import_batch.rows_duplicated = duplicate_count
        import_batch.rows_errors = summary.get('errors', 0)
        import_batch.status = "completed"
        import_batch.completed_at = datetime.utcnow()
        
        await db.commit()
        
        print(f"✅ Import completed: {inserted_count} imported, {duplicate_count} duplicates")
        
        # Prepare response
        summary.update({
            "rows_inserted": inserted_count,
            "rows_duplicated": duplicate_count,
            "batch_id": str(import_batch.id)
        })
        
        return ImportResponse(
            success=True,
            batch_id=str(import_batch.id),
            summary=summary,
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
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of transactions with filters"""
    
    print(f"📋 Transaction list request: page={page}, limit={limit}")
    print(f"👤 Current user: {current_user.email if current_user else 'None'}")
    
    if not current_user:
        print("❌ No authenticated user for transaction list")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Build query with filters
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
    
    # Add ordering and pagination
    query = query.order_by(desc(Transaction.posted_at))
    query = query.offset((page - 1) * limit).limit(limit)
    
    # Execute query with category relationship
    query = query.options(selectinload(Transaction.category))
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    print(f"✅ Found {len(transactions)} transactions")
    
    # Convert to response format
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
            source_category=transaction.source_category,
            import_batch_id=str(transaction.import_batch_id) if transaction.import_batch_id else None,
            created_at=transaction.created_at.isoformat()
        ))
    
    return response_data

@router.get("/summary")
async def get_transaction_summary(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get transaction summary statistics"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get total count
    count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
    count_result = await db.execute(count_query)
    total_transactions = count_result.scalar()
    
    # Get total amount
    sum_query = select(func.sum(Transaction.amount)).where(Transaction.user_id == current_user.id)
    sum_result = await db.execute(sum_query)
    total_amount = sum_result.scalar() or 0
    
    # Get date range
    date_query = select(
        func.min(Transaction.posted_at),
        func.max(Transaction.posted_at)
    ).where(Transaction.user_id == current_user.id)
    date_result = await db.execute(date_query)
    min_date, max_date = date_result.first()
    
    # Get categorization stats
    categorized_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.category_id.isnot(None)
        )
    )
    categorized_result = await db.execute(categorized_query)
    categorized_count = categorized_result.scalar()
    
    # Get recent imports
    recent_imports_query = select(ImportBatch).where(
        ImportBatch.user_id == current_user.id
    ).order_by(desc(ImportBatch.created_at)).limit(5)
    recent_imports_result = await db.execute(recent_imports_query)
    recent_imports = recent_imports_result.scalars().all()
    
    return {
        "total_transactions": total_transactions,
        "total_amount": float(total_amount),
        "categorized_count": categorized_count,
        "categorization_rate": categorized_count / total_transactions if total_transactions > 0 else 0,
        "date_range": {
            "earliest": min_date.isoformat() if min_date else None,
            "latest": max_date.isoformat() if max_date else None
        },
        "recent_imports": [
            {
                "id": str(batch.id),
                "filename": batch.filename,
                "rows_imported": batch.rows_imported,
                "status": batch.status,
                "created_at": batch.created_at.isoformat()
            }
            for batch in recent_imports
        ]
    }

@router.post("/categorize/{transaction_id}")
async def categorize_transaction(
    transaction_id: str,
    category_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually categorize a transaction"""
    
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
            Category.id == uuid.UUID(category_id),
            Category.user_id == current_user.id
        )
    )
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update transaction
    old_category_id = transaction.category_id
    transaction.category_id = uuid.UUID(category_id)
    transaction.source_category = "user"
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Transaction categorized as {category.name}"
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
    
    # Delete all transactions from this batch
    delete_query = select(Transaction).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.import_batch_id == uuid.UUID(batch_id)
        )
    )
    transactions_result = await db.execute(delete_query)
    transactions = transactions_result.scalars().all()
    
    for transaction in transactions:
        await db.delete(transaction)
    
    # Delete the batch
    await db.delete(batch)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Deleted {len(transactions)} transactions from batch {batch.filename}"
    }