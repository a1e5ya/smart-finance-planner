"""
Transaction analytics router - Analytics and summary endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from typing import Optional
from datetime import date, datetime, timedelta
import statistics

from ..models.database import get_db, User, Transaction, Category
from ..routers.transaction_queries import TransactionQueries, get_transaction_queries
from ..routers.transaction_models import (
    SpendingTrendsResponse, MerchantAnalysisResponse, 
    AnalyticsFilters, MerchantAnalyticsFilters
)
from ..routers.auth import get_current_user

router = APIRouter()

@router.get("/spending-trends", response_model=SpendingTrendsResponse)
async def get_spending_trends(
    months: int = Query(12, ge=1, le=24, description="Number of months to analyze"),
    category_id: Optional[str] = Query(None, description="Filter by specific category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get spending trends over time"""
    
    print(f"📊 Spending trends request: {months} months, category: {category_id}")
    
    queries = get_transaction_queries(db, current_user)
    trends = await queries.get_spending_trends(months, category_id)
    
    return SpendingTrendsResponse(
        trends=trends,
        months=len(trends),
        category_filter=category_id
    )

@router.get("/merchant-analysis", response_model=MerchantAnalysisResponse)
async def get_merchant_analysis(
    limit: int = Query(20, ge=5, le=100, description="Number of merchants to analyze"),
    min_transactions: int = Query(2, ge=1, description="Minimum transactions per merchant"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze spending patterns by merchant"""
    
    print(f"🏪 Merchant analysis: top {limit}, min {min_transactions} transactions")
    
    queries = get_transaction_queries(db, current_user)
    merchants = await queries.get_merchant_analysis(limit, min_transactions)
    
    return MerchantAnalysisResponse(
        merchants=merchants,
        analysis_criteria={
            "min_transactions": min_transactions,
            "limit": limit
        }
    )

@router.get("/category-breakdown")
async def get_category_breakdown(
    period: str = Query("month", regex="^(month|quarter|year)$", description="Analysis period"),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get spending breakdown by category"""
    
    from sqlalchemy import select, func, and_
    from ..models.database import Transaction, Category
    
    print(f"📈 Category breakdown: {period}, {start_date} to {end_date}")
    
    # Build base conditions
    conditions = [Transaction.user_id == current_user.id]
    
    if start_date:
        conditions.append(Transaction.posted_at >= start_date)
    if end_date:
        conditions.append(Transaction.posted_at <= end_date)
    
    # Query for category breakdown
    query = select(
        Category.name.label('category_name'),
        Category.icon.label('category_icon'),
        func.count(Transaction.id).label('transaction_count'),
        func.sum(func.abs(Transaction.amount)).label('total_amount'),
        func.avg(func.abs(Transaction.amount)).label('avg_amount'),
        Transaction.transaction_type
    ).join(
        Transaction, Transaction.category_id == Category.id
    ).where(
        and_(*conditions)
    ).group_by(
        Category.id, Category.name, Category.icon, Transaction.transaction_type
    ).order_by(func.sum(func.abs(Transaction.amount)).desc())
    
    result = await db.execute(query)
    
    # Process results
    categories = {}
    total_amount = 0
    
    for row in result:
        category_name = row.category_name
        transaction_type = row.transaction_type or 'unknown'
        amount = float(row.total_amount)
        
        if category_name not in categories:
            categories[category_name] = {
                "name": category_name,
                "icon": row.category_icon,
                "total_amount": 0,
                "transaction_count": 0,
                "avg_amount": 0,
                "by_type": {}
            }
        
        categories[category_name]["total_amount"] += amount
        categories[category_name]["transaction_count"] += row.transaction_count
        categories[category_name]["by_type"][transaction_type] = {
            "count": row.transaction_count,
            "amount": amount,
            "avg_amount": float(row.avg_amount)
        }
        
        total_amount += amount
    
    # Calculate percentages and finalize
    category_list = []
    for category_data in categories.values():
        category_data["percentage"] = (category_data["total_amount"] / total_amount * 100) if total_amount > 0 else 0
        category_data["avg_amount"] = category_data["total_amount"] / category_data["transaction_count"] if category_data["transaction_count"] > 0 else 0
        category_list.append(category_data)
    
    # Sort by total amount
    category_list.sort(key=lambda x: x["total_amount"], reverse=True)
    
    return {
        "categories": category_list,
        "summary": {
            "total_amount": total_amount,
            "total_categories": len(category_list),
            "period": period,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    }

@router.get("/monthly-summary")
async def get_monthly_summary(
    year: Optional[int] = Query(None, description="Specific year to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get monthly financial summary"""
    
    from sqlalchemy import select, func, and_, extract
    from ..models.database import Transaction
    from datetime import datetime
    
    print(f"📅 Monthly summary for year: {year or 'all years'}")
    
    # Use current year if not specified
    if not year:
        year = datetime.now().year
    
    conditions = [
        Transaction.user_id == current_user.id,
        extract('year', Transaction.posted_at) == year
    ]
    
    # Query for monthly data
    query = select(
        extract('month', Transaction.posted_at).label('month'),
        Transaction.transaction_type,
        func.count(Transaction.id).label('transaction_count'),
        func.sum(Transaction.amount).label('total_amount'),
        func.avg(Transaction.amount).label('avg_amount')
    ).where(
        and_(*conditions)
    ).group_by(
        extract('month', Transaction.posted_at),
        Transaction.transaction_type
    ).order_by('month')
    
    result = await db.execute(query)
    
    # Process results into monthly structure
    months = {}
    for month_num in range(1, 13):
        months[month_num] = {
            "month": month_num,
            "month_name": datetime(year, month_num, 1).strftime('%B'),
            "income": 0,
            "expenses": 0,
            "transfers": 0,
            "net_flow": 0,
            "transaction_count": 0,
            "by_type": {}
        }
    
    for row in result:
        month_num = int(row.month)
        transaction_type = row.transaction_type or 'unknown'
        amount = float(row.total_amount)
        count = row.transaction_count
        
        if month_num in months:
            months[month_num]["by_type"][transaction_type] = {
                "count": count,
                "amount": amount,
                "avg_amount": float(row.avg_amount)
            }
            months[month_num]["transaction_count"] += count
            
            if transaction_type == 'income':
                months[month_num]["income"] = amount
            elif transaction_type == 'expense':
                months[month_num]["expenses"] = abs(amount)  # Make positive
            elif transaction_type == 'transfer':
                months[month_num]["transfers"] = amount
    
    # Calculate net flow for each month
    for month_data in months.values():
        month_data["net_flow"] = month_data["income"] - month_data["expenses"]
    
    # Calculate year totals
    year_summary = {
        "total_income": sum(m["income"] for m in months.values()),
        "total_expenses": sum(m["expenses"] for m in months.values()),
        "total_transfers": sum(m["transfers"] for m in months.values()),
        "net_savings": sum(m["net_flow"] for m in months.values()),
        "total_transactions": sum(m["transaction_count"] for m in months.values()),
        "avg_monthly_income": sum(m["income"] for m in months.values()) / 12,
        "avg_monthly_expenses": sum(m["expenses"] for m in months.values()) / 12,
        "savings_rate": 0
    }
    
    if year_summary["total_income"] > 0:
        year_summary["savings_rate"] = (year_summary["net_savings"] / year_summary["total_income"]) * 100
    
    return {
        "year": year,
        "months": list(months.values()),
        "year_summary": year_summary
    }

@router.get("/financial-health")
async def get_financial_health_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get financial health indicators and metrics"""
    
    from sqlalchemy import select, func, and_
    from ..models.database import Transaction
    from datetime import datetime, timedelta
    
    print(f"💰 Financial health metrics for: {current_user.email}")
    
    # Get data for last 12 months
    one_year_ago = datetime.now() - timedelta(days=365)
    
    conditions = [
        Transaction.user_id == current_user.id,
        Transaction.posted_at >= one_year_ago
    ]
    
    # Query for basic metrics
    metrics_query = select(
        Transaction.transaction_type,
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('total'),
        func.avg(Transaction.amount).label('average')
    ).where(
        and_(*conditions)
    ).group_by(Transaction.transaction_type)
    
    result = await db.execute(metrics_query)
    
    income_total = 0
    expense_total = 0
    transfer_total = 0
    
    for row in result:
        transaction_type = row.transaction_type or 'unknown'
        total = float(row.total or 0)
        
        if transaction_type == 'income':
            income_total = total
        elif transaction_type == 'expense':
            expense_total = abs(total)
        elif transaction_type == 'transfer':
            transfer_total = total
    
    # Calculate key metrics
    net_income = income_total - expense_total
    savings_rate = (net_income / income_total * 100) if income_total > 0 else 0
    
    # Get monthly variance (expense consistency)
    monthly_variance_query = select(
        func.extract('year', Transaction.posted_at).label('year'),
        func.extract('month', Transaction.posted_at).label('month'),
        func.sum(func.abs(Transaction.amount)).label('monthly_expenses')
    ).where(
        and_(*conditions, Transaction.transaction_type == 'expense')
    ).group_by(
        func.extract('year', Transaction.posted_at),
        func.extract('month', Transaction.posted_at)
    )
    
    variance_result = await db.execute(monthly_variance_query)
    monthly_expenses = [float(row.monthly_expenses) for row in variance_result]
    
    # Calculate expense variance
    if len(monthly_expenses) > 1:
        import statistics
        expense_variance = statistics.variance(monthly_expenses)
        expense_std_dev = statistics.stdev(monthly_expenses)
        avg_monthly_expense = statistics.mean(monthly_expenses)
        expense_consistency = max(0, 100 - (expense_std_dev / avg_monthly_expense * 100)) if avg_monthly_expense > 0 else 0
    else:
        expense_variance = 0
        expense_consistency = 100
    
    # Health score calculation (0-100)
    health_score = 0
    
    # Savings rate component (40% of score)
    if savings_rate >= 20:
        health_score += 40
    elif savings_rate >= 10:
        health_score += 30
    elif savings_rate >= 0:
        health_score += 20
    
    # Expense consistency (30% of score)
    health_score += (expense_consistency * 0.3)
    
    # Income stability (30% of score) - simplified for now
    if income_total > 0:
        health_score += 30
    
    health_score = min(100, max(0, health_score))
    
    # Determine health status
    if health_score >= 80:
        health_status = "excellent"
    elif health_score >= 60:
        health_status = "good"
    elif health_score >= 40:
        health_status = "fair"
    else:
        health_status = "needs_improvement"
    
    # Generate recommendations
    recommendations = []
    if savings_rate < 10:
        recommendations.append("Consider increasing your savings rate to at least 10% of income")
    if expense_consistency < 70:
        recommendations.append("Try to maintain more consistent monthly expenses")
    if savings_rate < 0:
        recommendations.append("You're spending more than you earn - review your budget")
    if len(recommendations) == 0:
        recommendations.append("Great job! Keep maintaining your financial habits")
    
    return {
        "health_score": round(health_score, 1),
        "health_status": health_status,
        "metrics": {
            "savings_rate": round(savings_rate, 1),
            "expense_consistency": round(expense_consistency, 1),
            "monthly_net_income": round(net_income / 12, 2),
            "monthly_avg_expenses": round(sum(monthly_expenses) / len(monthly_expenses), 2) if monthly_expenses else 0
        },
        "financial_summary": {
            "total_income_12m": round(income_total, 2),
            "total_expenses_12m": round(expense_total, 2),
            "net_savings_12m": round(net_income, 2),
            "avg_monthly_income": round(income_total / 12, 2),
            "avg_monthly_expenses": round(expense_total / 12, 2)
        },
        "recommendations": recommendations,
        "analysis_period": {
            "start_date": one_year_ago.isoformat(),
            "end_date": datetime.now().isoformat(),
            "months_analyzed": len(monthly_expenses)
        }
    }

@router.get("/compare-periods")
async def compare_time_periods(
    period1_start: date = Query(..., description="Start date of first period"),
    period1_end: date = Query(..., description="End date of first period"),
    period2_start: date = Query(..., description="Start date of second period"),
    period2_end: date = Query(..., description="End date of second period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare financial metrics between two time periods"""
    
    from sqlalchemy import select, func, and_
    from ..models.database import Transaction
    
    print(f"🔄 Comparing periods: {period1_start}-{period1_end} vs {period2_start}-{period2_end}")
    
    async def get_period_metrics(start_date: date, end_date: date):
        """Get metrics for a specific period"""
        
        conditions = [
            Transaction.user_id == current_user.id,
            Transaction.posted_at >= start_date,
            Transaction.posted_at <= end_date
        ]
        
        query = select(
            Transaction.transaction_type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total'),
            func.avg(Transaction.amount).label('average')
        ).where(and_(*conditions)).group_by(Transaction.transaction_type)
        
        result = await db.execute(query)
        
        metrics = {
            'income': 0,
            'expenses': 0,
            'transfers': 0,
            'transaction_count': 0,
            'net_flow': 0
        }
        
        for row in result:
            transaction_type = row.transaction_type or 'unknown'
            total = float(row.total or 0)
            count = row.count
            
            metrics['transaction_count'] += count
            
            if transaction_type == 'income':
                metrics['income'] = total
            elif transaction_type == 'expense':
                metrics['expenses'] = abs(total)
            elif transaction_type == 'transfer':
                metrics['transfers'] = total
        
        metrics['net_flow'] = metrics['income'] - metrics['expenses']
        metrics['savings_rate'] = (metrics['net_flow'] / metrics['income'] * 100) if metrics['income'] > 0 else 0
        
        return metrics
    
    # Get metrics for both periods
    period1_metrics = await get_period_metrics(period1_start, period1_end)
    period2_metrics = await get_period_metrics(period2_start, period2_end)
    
    # Calculate changes
    def calculate_change(old_value, new_value):
        if old_value == 0:
            return 0 if new_value == 0 else 100
        return ((new_value - old_value) / old_value) * 100
    
    changes = {
        'income_change': calculate_change(period1_metrics['income'], period2_metrics['income']),
        'expenses_change': calculate_change(period1_metrics['expenses'], period2_metrics['expenses']),
        'net_flow_change': calculate_change(period1_metrics['net_flow'], period2_metrics['net_flow']),
        'savings_rate_change': period2_metrics['savings_rate'] - period1_metrics['savings_rate'],
        'transaction_count_change': calculate_change(period1_metrics['transaction_count'], period2_metrics['transaction_count'])
    }
    
    return {
        "period1": {
            "date_range": {
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat()
            },
            "metrics": period1_metrics
        },
        "period2": {
            "date_range": {
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat()
            },
            "metrics": period2_metrics
        },
        "comparison": {
            "changes": changes,
            "improvement_areas": [
                "Income increased" if changes['income_change'] > 5 else "Income decreased" if changes['income_change'] < -5 else None,
                "Expenses reduced" if changes['expenses_change'] < -5 else "Expenses increased" if changes['expenses_change'] > 5 else None,
                "Savings improved" if changes['net_flow_change'] > 10 else "Savings declined" if changes['net_flow_change'] < -10 else None
            ]
        }
    }