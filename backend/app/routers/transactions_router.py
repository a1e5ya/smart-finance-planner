"""
Main transactions router with CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import date, datetime
import uuid

from ..models.database import get_db, User, Transaction, Category, AuditLog
from ..services.transaction_service import TransactionService, get_transaction_service
from ..routers.transaction_queries import TransactionQueries, get_transaction_queries
from ..routers.transaction_models import (
    TransactionResponse, TransactionSummary, DeleteResponse,
    CategoryAssignment, TransactionUpdate, BulkCategorizeRequest,
    TransactionFilters, ReviewTransactionsResponse, BulkOperationResponse
)
from ..routers.auth import get_current_user

router = APIRouter()

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of transactions with enhanced filters"""
    
    print(f"📋 Transaction list request: page={page}, limit={limit}")
    print(f"👤 Current user: {current_user.email if current_user else 'None'}")
    
    # Create filters object
    filters = TransactionFilters(
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        merchant=merchant,
        category_id=category_id,
        account_id=account_id,
        transaction_type=transaction_type,
        review_needed=review_needed,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get transactions using queries service
    queries = get_transaction_queries(db, current_user)
    transactions, total_count = await queries.get_transactions_with_filters(filters)
    
    print(f"✅ Found {len(transactions)} transactions (total: {total_count})")
    
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive transaction summary with analytics"""
    
    print(f"📊 Transaction summary request for user: {current_user.email}")
    
    queries = get_transaction_queries(db, current_user)
    summary_data = await queries.get_transaction_summary(start_date, end_date)
    
    return TransactionSummary(**summary_data)

@router.get("/review", response_model=ReviewTransactionsResponse)
async def get_transactions_needing_review(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get transactions that need manual review"""
    
    print(f"🔍 Review transactions request: page={page}, limit={limit}")
    
    queries = get_transaction_queries(db, current_user)
    transactions, total_count = await queries.get_transactions_needing_review(page, limit)
    
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
    
    return ReviewTransactionsResponse(
        transactions=response_data,
        total_count=total_count,
        page=page,
        limit=limit,
        has_more=len(response_data) == limit
    )

@router.post("/categorize/{transaction_id}")
async def categorize_transaction(
    transaction_id: str,
    assignment: CategoryAssignment,
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Manually categorize a transaction with enhanced error handling"""
    
    print(f"🏷️ Categorize transaction: {transaction_id} -> {assignment.category_id}")
    
    result = await transaction_service.categorize_transaction(
        transaction_id=transaction_id,
        category_id=assignment.category_id,
        confidence=assignment.confidence or 1.0,
        notes=assignment.notes
    )
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        elif "access denied" in result["message"].lower():
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    return JSONResponse(
        content=result,
        status_code=200
    )

@router.post("/bulk-categorize", response_model=BulkOperationResponse)
async def bulk_categorize_transactions(
    request: BulkCategorizeRequest,
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Bulk categorize multiple transactions"""
    
    print(f"🏷️ Bulk categorize: {len(request.transaction_ids)} transactions -> {request.category_id}")
    
    result = await transaction_service.bulk_categorize_transactions(
        transaction_ids=request.transaction_ids,
        category_id=request.category_id,
        confidence=request.confidence
    )
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        elif "access denied" in result["message"].lower():
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return BulkOperationResponse(
        success=result["success"],
        message=result["message"],
        updated_count=result["updated_count"]
    )

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update transaction details"""
    
    print(f"✏️ Update transaction: {transaction_id}")
    
    queries = get_transaction_queries(db, current_user)
    transaction = await queries.get_transaction_by_id(transaction_id)
    
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
        from sqlalchemy import select
        from ..models.database import Category
        import uuid
        
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
    from ..models.database import AuditLog
    from datetime import datetime
    
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

@router.delete("/{transaction_id}", response_model=DeleteResponse)
async def delete_transaction(
    transaction_id: str,
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Delete a single transaction"""
    
    print(f"🗑️ Delete transaction request: {transaction_id}")
    
    result = await transaction_service.delete_transaction(transaction_id)
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    return DeleteResponse(**result)

@router.delete("/batch/{batch_id}")
async def delete_import_batch(
    batch_id: str,
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Delete an import batch and all its transactions"""
    
    print(f"🗑️ Delete import batch: {batch_id}")
    
    result = await transaction_service.delete_import_batch(batch_id)
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    return JSONResponse(
        content={
            "success": result["success"],
            "message": result["message"],
            "deleted_count": result["deleted_count"]
        },
        status_code=200
    )

@router.post("/reset")
async def reset_all_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset all transaction data for the current user"""
    
    try:
        from sqlalchemy import delete
        from ..models.database import Transaction, ImportBatch
        
        # Count transactions before deletion
        count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
        count_result = await db.execute(count_query)
        transaction_count = count_result.scalar()
        
        # Delete all transactions for this user
        delete_transactions = delete(Transaction).where(Transaction.user_id == current_user.id)
        await db.execute(delete_transactions)
        
        # Delete all import batches for this user
        delete_batches = delete(ImportBatch).where(ImportBatch.user_id == current_user.id)
        await db.execute(delete_batches)
        
        await db.commit()
        
        # Log the reset action
        audit_entry = AuditLog(
            user_id=current_user.id,
            firebase_uid=current_user.firebase_uid,
            entity="transaction",
            action="reset_all",
            details={
                "transactions_deleted": transaction_count,
                "reason": "user_requested_reset"
            }
        )
        db.add(audit_entry)
        await db.commit()
        
        print(f"✅ Reset complete: {transaction_count} transactions deleted for user {current_user.email}")
        
        return {
            "success": True,
            "message": f"Successfully deleted {transaction_count} transactions",
            "deleted_count": transaction_count
        }
        
    except Exception as e:
        print(f"❌ Reset failed for user {current_user.email}: {e}")
        await db.rollback()
        return {
            "success": False,
            "message": f"Reset failed: {str(e)}",
            "deleted_count": 0
        }