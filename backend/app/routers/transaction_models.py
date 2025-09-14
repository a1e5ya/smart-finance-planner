"""
Pydantic models for transaction-related API requests and responses
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date

# Response Models
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

class ImportResponse(BaseModel):
    success: bool
    batch_id: str
    summary: Dict[str, Any]
    message: str

class DeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int = 1

class SpendingTrendsResponse(BaseModel):
    trends: List[Dict[str, Any]]
    months: int
    category_filter: Optional[str]

class MerchantAnalysisResponse(BaseModel):
    merchants: List[Dict[str, Any]]
    analysis_criteria: Dict[str, Any]

class ReviewTransactionsResponse(BaseModel):
    transactions: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    has_more: bool

class BulkOperationResponse(BaseModel):
    success: bool
    message: str
    updated_count: int

# Request Models
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

class BulkCategorizeRequest(BaseModel):
    transaction_ids: List[str]
    category_id: str
    confidence: float = 1.0

class TransactionFilters(BaseModel):
    page: int = 1
    limit: int = 50
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    merchant: Optional[str] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    transaction_type: Optional[str] = None
    review_needed: Optional[bool] = None
    sort_by: str = "posted_at"
    sort_order: str = "desc"

class ImportFilters(BaseModel):
    account_name: Optional[str] = "Default Account"
    account_type: Optional[str] = "checking"
    auto_categorize: bool = True

class AnalyticsFilters(BaseModel):
    months: int = 12
    category_id: Optional[str] = None

class MerchantAnalyticsFilters(BaseModel):
    limit: int = 20
    min_transactions: int = 2

# Utility Models
class DateRange(BaseModel):
    earliest: Optional[str]
    latest: Optional[str]

class TransactionTypeBreakdown(BaseModel):
    income: int = 0
    expense: int = 0
    transfer: int = 0
    unknown: int = 0

class CategoryDistribution(BaseModel):
    category_name: str
    count: int
    total_amount: float

class MerchantStats(BaseModel):
    merchant: str
    transaction_count: int
    total_amount: float
    average_amount: float
    frequency_per_month: float
    first_transaction: str
    last_transaction: str

class ImportBatchInfo(BaseModel):
    id: str
    filename: str
    rows_imported: int
    status: str
    created_at: str

class OperationResult(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None