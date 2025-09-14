"""
Transaction import router - CSV import specific endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..models.database import get_db, User
from ..services.transaction_import_service import TransactionImportService, get_import_service
from .transaction_models import ImportResponse, ImportFilters
from .auth import get_current_user

router = APIRouter()

@router.post("/import")
async def import_transactions(
    file: UploadFile = File(...),
    account_name: Optional[str] = Form("Default Account"),
    account_type: Optional[str] = Form("checking"),
    auto_categorize: bool = Form(True),
    current_user: User = Depends(get_current_user),
    import_service: TransactionImportService = Depends(get_import_service)
):
    """Import transactions from CSV file with enhanced processing and auto-categorization"""
    
    print(f"📤 Import request received: {file.filename}")
    print(f"👤 Current user: {current_user.email}")
    print(f"🏷️ Auto categorization: {auto_categorize}")
    
    # Validate file
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")
    
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Process import
    result = await import_service.import_from_csv(
        file_content=file_content,
        filename=file.filename,
        account_name=account_name,
        account_type=account_type,
        auto_categorize=auto_categorize
    )
    
    if not result["success"]:
        if "duplicate_file" in result.get("summary", {}):
            raise HTTPException(status_code=409, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    return result

@router.post("/create-default-mappings")
async def create_default_category_mappings(
    current_user: User = Depends(get_current_user),
    import_service: TransactionImportService = Depends(get_import_service)
):
    """Create default category mappings for better auto-categorization"""
    
    print(f"🏷️ Creating default mappings for user: {current_user.email}")
    
    try:
        created_count = await import_service.create_default_category_mappings()
        
        return {
            "success": True,
            "message": f"Created {created_count} default category mappings",
            "mappings_created": created_count
        }
        
    except Exception as e:
        print(f"❌ Failed to create default mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create mappings: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """Get information about supported file formats"""
    
    return {
        "supported_formats": [
            {
                "extension": ".csv",
                "mime_types": ["text/csv", "application/csv"],
                "description": "Comma-separated values file",
                "max_size_mb": 10,
                "encoding": "UTF-8, UTF-8-BOM, Latin-1, CP1252"
            },
            {
                "extension": ".xlsx",
                "mime_types": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
                "description": "Excel spreadsheet file",
                "max_size_mb": 10,
                "encoding": "Excel format"
            }
        ],
        "expected_columns": [
            "Date", "Amount", "Merchant", "Message", "Full_Description",
            "Main_Category", "Category", "Subcategory", "Account", "Owner",
            "Account_Type", "Amount_Abs", "Is_Expense", "Is_Income",
            "Year", "Month", "Year_Month", "Weekday", "Transfer_Pair_ID"
        ],
        "required_columns": ["Date", "Amount"],
        "auto_categorization": {
            "enabled": True,
            "methods": ["csv_mapping", "rule_based", "keyword_matching"],
            "confidence_threshold": 0.8
        }
    }

@router.get("/import-history")
async def get_import_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's import history"""
    
    from sqlalchemy import select, desc
    from ..models.database import ImportBatch
    
    query = select(ImportBatch).where(
        ImportBatch.user_id == current_user.id
    ).order_by(desc(ImportBatch.created_at)).limit(limit)
    
    result = await db.execute(query)
    batches = result.scalars().all()
    
    import_history = []
    for batch in batches:
        import_history.append({
            "id": str(batch.id),
            "filename": batch.filename,
            "file_size": batch.file_size,
            "status": batch.status,
            "rows_total": batch.rows_total,
            "rows_imported": batch.rows_imported,
            "rows_duplicated": batch.rows_duplicated,
            "rows_errors": batch.rows_errors,
            "auto_categorized": batch.summary_data.get("auto_categorized_count", 0) if batch.summary_data else 0,
            "created_at": batch.created_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "error_message": batch.error_message
        })
    
    return {
        "import_history": import_history,
        "total_imports": len(import_history)
    }

@router.get("/batch/{batch_id}/details")
async def get_import_batch_details(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific import batch"""
    
    from sqlalchemy import select, and_, func
    from ..models.database import ImportBatch, Transaction
    import uuid
    
    # Get batch info
    batch_query = select(ImportBatch).where(
        and_(
            ImportBatch.id == uuid.UUID(batch_id),
            ImportBatch.user_id == current_user.id
        )
    )
    batch_result = await db.execute(batch_query)
    batch = batch_result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    
    # Get transaction statistics for this batch
    stats_query = select(
        func.count(Transaction.id).label('total_transactions'),
        func.sum(func.case((Transaction.category_id.isnot(None), 1), else_=0)).label('categorized'),
        func.sum(func.case((Transaction.review_needed == True, 1), else_=0)).label('needs_review'),
        func.sum(Transaction.amount).label('total_amount')
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.import_batch_id == uuid.UUID(batch_id)
        )
    )
    
    stats_result = await db.execute(stats_query)
    stats = stats_result.first()
    
    # Get transaction type breakdown
    type_query = select(
        Transaction.transaction_type,
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('amount')
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.import_batch_id == uuid.UUID(batch_id)
        )
    ).group_by(Transaction.transaction_type)
    
    type_result = await db.execute(type_query)
    type_breakdown = {}
    
    for row in type_result:
        type_breakdown[row.transaction_type or 'unknown'] = {
            "count": row.count,
            "amount": float(row.amount or 0)
        }
    
    return {
        "batch_info": {
            "id": str(batch.id),
            "filename": batch.filename,
            "file_size": batch.file_size,
            "file_hash": batch.file_hash,
            "status": batch.status,
            "created_at": batch.created_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "error_message": batch.error_message
        },
        "processing_summary": {
            "rows_total": batch.rows_total,
            "rows_imported": batch.rows_imported,
            "rows_duplicated": batch.rows_duplicated,
            "rows_errors": batch.rows_errors,
            "success_rate": (batch.rows_imported / batch.rows_total) if batch.rows_total > 0 else 0
        },
        "categorization_summary": {
            "total_transactions": int(stats.total_transactions or 0),
            "categorized": int(stats.categorized or 0),
            "needs_review": int(stats.needs_review or 0),
            "categorization_rate": (stats.categorized / stats.total_transactions) if stats.total_transactions > 0 else 0,
            "auto_categorized": batch.summary_data.get("auto_categorized_count", 0) if batch.summary_data else 0
        },
        "financial_summary": {
            "total_amount": float(stats.total_amount or 0),
            "by_type": type_breakdown
        },
        "detailed_summary": batch.summary_data or {}
    }

@router.post("/validate-file")
async def validate_import_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Validate CSV file format without importing"""
    
    print(f"🔍 Validating file: {file.filename}")
    
    # Basic validation
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")
    
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Read a small portion to validate format
        file_content = await file.read(1024 * 100)  # Read first 100KB
        await file.seek(0)  # Reset file pointer
        
        # Try to parse the beginning of the file
        from ..services.csv_processor import EnhancedCSVProcessor
        
        processor = EnhancedCSVProcessor()
        
        try:
            # Just try to detect encoding and parse headers
            if isinstance(file_content, bytes):
                content = processor.detect_file_encoding(file_content)
            else:
                content = file_content
            
            # Get first few lines to check format
            lines = content.split('\n')[:5]
            
            validation_result = {
                "valid": True,
                "filename": file.filename,
                "file_size": file.size,
                "estimated_rows": len(lines) - 1 if len(lines) > 1 else 0,
                "sample_headers": lines[0].split(',') if lines else [],
                "encoding_detected": True,
                "warnings": [],
                "recommendations": []
            }
            
            # Add recommendations
            if len(validation_result["sample_headers"]) < 3:
                validation_result["warnings"].append("File appears to have very few columns")
            
            if not any("date" in header.lower() for header in validation_result["sample_headers"]):
                validation_result["warnings"].append("No date column detected")
            
            if not any("amount" in header.lower() for header in validation_result["sample_headers"]):
                validation_result["warnings"].append("No amount column detected")
            
            validation_result["recommendations"].append("Ensure your CSV has Date and Amount columns")
            validation_result["recommendations"].append("UTF-8 encoding is recommended for best results")
            
            return validation_result
            
        except Exception as parse_error:
            return {
                "valid": False,
                "filename": file.filename,
                "file_size": file.size,
                "error": f"Failed to parse file: {str(parse_error)}",
                "recommendations": [
                    "Check that the file is a valid CSV or XLSX format",
                    "Ensure the file is not corrupted",
                    "Try saving the file with UTF-8 encoding"
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")