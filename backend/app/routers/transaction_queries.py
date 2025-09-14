"""
Database queries for transaction operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime, date

from ..models.database import (
    Transaction, Account, Category, ImportBatch, User, Budget, Goal
)
from ..routers.transaction_models import TransactionFilters, AnalyticsFilters, MerchantAnalyticsFilters

class TransactionQueries:
    """Database queries for transaction operations"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get a single transaction by ID with user verification"""
        query = select(Transaction).options(selectinload(Transaction.category)).where(
            and_(
                Transaction.id == uuid.UUID(transaction_id),
                Transaction.user_id == self.user.id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_transactions_with_filters(
        self, 
        filters: TransactionFilters
    ) -> Tuple[List[Transaction], int]:
        """Get transactions with filters and pagination"""
        
        # Build base query
        query = select(Transaction).where(Transaction.user_id == self.user.id)
        count_query = select(func.count(Transaction.id)).where(Transaction.user_id == self.user.id)
        
        # Apply filters
        filter_conditions = self._build_filter_conditions(filters)
        if filter_conditions:
            query = query.where(and_(*filter_conditions))
            count_query = count_query.where(and_(*filter_conditions))
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply sorting
        sort_column = getattr(Transaction, filters.sort_by, Transaction.posted_at)
        if filters.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Add secondary sort by created_at for consistency
        if filters.sort_by != "created_at":
            query = query.order_by(desc(Transaction.created_at))
        
        # Apply pagination
        query = query.offset((filters.page - 1) * filters.limit).limit(filters.limit)
        
        # Include category relationship
        query = query.options(selectinload(Transaction.category))
        
        # Execute query
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        return transactions, total_count
    
    async def get_transaction_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get comprehensive transaction summary"""
        
        base_conditions = [Transaction.user_id == self.user.id]
        
        if start_date:
            base_conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            base_conditions.append(Transaction.posted_at <= end_date)
        
        base_condition = and_(*base_conditions)
        
        # Get total count
        count_query = select(func.count(Transaction.id)).where(base_condition)
        count_result = await self.db.execute(count_query)
        total_transactions = count_result.scalar()
        
        # Get amounts by type
        amounts_query = select(
            Transaction.transaction_type,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('count')
        ).where(base_condition).group_by(Transaction.transaction_type)
        
        amounts_result = await self.db.execute(amounts_query)
        
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
                expense_amount = abs(amount)
            elif trans_type == 'transfer':
                transfer_amount = amount
        
        # Get date range
        date_query = select(
            func.min(Transaction.posted_at),
            func.max(Transaction.posted_at)
        ).where(base_condition)
        
        date_result = await self.db.execute(date_query)
        min_date, max_date = date_result.first()
        
        # Get categorization stats
        categorized_query = select(func.count(Transaction.id)).where(
            and_(base_condition, Transaction.category_id.isnot(None))
        )
        categorized_result = await self.db.execute(categorized_query)
        categorized_count = categorized_result.scalar()
        
        # Get spending by month
        monthly_query = select(
            Transaction.year_month,
            func.sum(Transaction.amount).label('amount')
        ).where(
            and_(base_condition, Transaction.transaction_type == 'expense')
        ).group_by(Transaction.year_month).order_by(Transaction.year_month)
        
        monthly_result = await self.db.execute(monthly_query)
        by_month = {row.year_month: float(abs(row.amount)) for row in monthly_result if row.year_month}
        
        # Get top merchants
        merchants_query = select(
            Transaction.merchant,
            func.count(Transaction.id).label('count'),
            func.sum(func.abs(Transaction.amount)).label('total')
        ).where(
            and_(base_condition, Transaction.merchant.isnot(None), Transaction.merchant != '')
        ).group_by(Transaction.merchant).order_by(desc('total')).limit(10)
        
        merchants_result = await self.db.execute(merchants_query)
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
            base_condition
        ).group_by(Category.id, Category.name, Category.icon).order_by(desc('total')).limit(10)
        
        categories_result = await self.db.execute(categories_query)
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
            ImportBatch.user_id == self.user.id
        ).order_by(desc(ImportBatch.created_at)).limit(5)
        
        recent_imports_result = await self.db.execute(recent_imports_query)
        recent_imports = recent_imports_result.scalars().all()
        
        return {
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "income_amount": income_amount,
            "expense_amount": expense_amount,
            "transfer_amount": transfer_amount,
            "categorized_count": categorized_count,
            "categorization_rate": categorized_count / total_transactions if total_transactions > 0 else 0,
            "date_range": {
                "earliest": min_date.isoformat() if min_date else None,
                "latest": max_date.isoformat() if max_date else None
            },
            "by_type": by_type,
            "by_month": by_month,
            "top_merchants": top_merchants,
            "top_categories": top_categories,
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
    
    async def get_transactions_needing_review(
        self,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[Transaction], int]:
        """Get transactions that need manual review"""
        
        # Base query for review needed transactions
        base_condition = and_(
            Transaction.user_id == self.user.id,
            Transaction.review_needed == True
        )
        
        # Get total count
        count_query = select(func.count(Transaction.id)).where(base_condition)
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get transactions with pagination
        query = select(Transaction).where(base_condition).order_by(desc(Transaction.posted_at))
        query = query.offset((page - 1) * limit).limit(limit)
        query = query.options(selectinload(Transaction.category))
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        return transactions, total_count
    
    async def get_spending_trends(
        self,
        months: int = 12,
        category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get spending trends over time"""
        
        conditions = [
            Transaction.user_id == self.user.id,
            Transaction.transaction_type == 'expense'
        ]
        
        if category_id:
            conditions.append(Transaction.category_id == uuid.UUID(category_id))
        
        query = select(
            Transaction.year_month,
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).where(
            and_(*conditions)
        ).group_by(Transaction.year_month).order_by(Transaction.year_month.desc()).limit(months)
        
        result = await self.db.execute(query)
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
        return trends
    
    async def get_merchant_analysis(
        self,
        limit: int = 20,
        min_transactions: int = 2
    ) -> List[Dict[str, Any]]:
        """Analyze spending patterns by merchant"""
        
        query = select(
            Transaction.merchant,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.avg(func.abs(Transaction.amount)).label('avg_amount'),
            func.min(Transaction.posted_at).label('first_transaction'),
            func.max(Transaction.posted_at).label('last_transaction')
        ).where(
            and_(
                Transaction.user_id == self.user.id,
                Transaction.merchant.isnot(None),
                Transaction.merchant != ''
            )
        ).group_by(Transaction.merchant).having(
            func.count(Transaction.id) >= min_transactions
        ).order_by(desc('total_amount')).limit(limit)
        
        result = await self.db.execute(query)
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
        
        return merchants
    
    def _build_filter_conditions(self, filters: TransactionFilters) -> List:
        """Build filter conditions for transaction queries"""
        conditions = []
        
        if filters.start_date:
            conditions.append(Transaction.posted_at >= filters.start_date)
        if filters.end_date:
            conditions.append(Transaction.posted_at <= filters.end_date)
        if filters.min_amount is not None:
            conditions.append(Transaction.amount >= filters.min_amount)
        if filters.max_amount is not None:
            conditions.append(Transaction.amount <= filters.max_amount)
        if filters.merchant:
            conditions.append(Transaction.merchant.ilike(f"%{filters.merchant}%"))
        if filters.category_id:
            conditions.append(Transaction.category_id == uuid.UUID(filters.category_id))
        if filters.account_id:
            conditions.append(Transaction.account_id == uuid.UUID(filters.account_id))
        if filters.transaction_type:
            conditions.append(Transaction.transaction_type == filters.transaction_type)
        if filters.review_needed is not None:
            conditions.append(Transaction.review_needed == filters.review_needed)
        
        return conditions

# Helper function to create queries instance
def get_transaction_queries(db: AsyncSession, user: User) -> TransactionQueries:
    """Get transaction queries instance"""
    return TransactionQueries(db, user)