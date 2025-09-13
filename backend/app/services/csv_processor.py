import pandas as pd
import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Tuple, Optional, Union
import re
from io import StringIO, BytesIO

class CSVProcessor:
    """Process CSV files with the specific format from your sample data"""
    
    # Expected columns from your sample CSV
    EXPECTED_COLUMNS = {
        "date": "Date",
        "amount": "Amount", 
        "merchant": "Merchant",
        "message": "Message",
        "full_description": "Full_Description",
        "main_category": "Main_Category",
        "category": "Category",
        "subcategory": "Subcategory",
        "account": "Account",
        "owner": "Owner",
        "account_type": "Account_Type",
        "amount_abs": "Amount_Abs",
        "is_expense": "Is_Expense",
        "is_income": "Is_Income",
        "year": "Year",
        "month": "Month",
        "year_month": "Year_Month",
        "weekday": "Weekday",
        "transfer_pair_id": "Transfer_Pair_ID"
    }
    
    # Date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y/%m/%d",
        "%m-%d-%Y",
        "%m-%d-%y",
        "%d-%m-%Y",
        "%d-%m-%y"
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def parse_csv_file(self, file_content: Union[str, bytes], filename: str) -> pd.DataFrame:
        """Parse CSV file content into a pandas DataFrame"""
        try:
            # Handle bytes or string content
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Try different separators
            separators = [',', ';', '\t', '|']
            df = None
            
            for sep in separators:
                try:
                    df = pd.read_csv(StringIO(file_content), separator=sep)
                    if len(df.columns) > 1:  # Valid if more than 1 column
                        break
                except:
                    continue
            
            if df is None or len(df.columns) <= 1:
                raise ValueError("Could not parse CSV file with any common separator")
            
            # Clean column names - remove extra whitespace
            df.columns = [col.strip() for col in df.columns]
            
            # Remove empty rows
            df = df.dropna(how='all')
            
            # Validate required columns exist
            missing_columns = []
            for key, expected_col in self.EXPECTED_COLUMNS.items():
                if expected_col not in df.columns:
                    missing_columns.append(expected_col)
            
            if missing_columns:
                self.warnings.append(f"Missing expected columns: {missing_columns}")
                # Check if we have at least the basic required columns
                required_basic = ["Date", "Amount", "Merchant"]
                missing_basic = [col for col in required_basic if col not in df.columns]
                if missing_basic:
                    raise ValueError(f"Missing required columns: {missing_basic}")
            
            return df
            
        except Exception as e:
            self.errors.append(f"Failed to parse CSV: {str(e)}")
            raise ValueError(f"CSV parsing failed: {str(e)}")
    
    def normalize_date(self, date_str: str) -> Optional[datetime]:
        """Normalize date string to datetime object"""
        if pd.isna(date_str) or not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        self.warnings.append(f"Could not parse date: {date_str}")
        return None
    
    def normalize_amount(self, amount_str: Union[str, int, float]) -> Optional[Decimal]:
        """Normalize amount to Decimal"""
        if pd.isna(amount_str) or amount_str == '':
            return None
        
        # Convert to string and clean
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and spaces
        amount_str = re.sub(r'[$€£¥,\s]', '', amount_str)
        
        # Handle parentheses as negative (common in accounting)
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = '-' + amount_str[1:-1]
        
        try:
            return Decimal(str(amount_str))
        except:
            self.warnings.append(f"Could not parse amount: {amount_str}")
            return None
    
    def normalize_merchant(self, merchant_str: str) -> str:
        """Clean and normalize merchant name"""
        if pd.isna(merchant_str) or not merchant_str:
            return ""
        
        merchant = str(merchant_str).strip()
        
        # Remove extra whitespace
        merchant = re.sub(r'\s+', ' ', merchant)
        
        # Common cleanup patterns
        merchant = re.sub(r'\*+', '', merchant)  # Remove asterisks
        merchant = re.sub(r'^\d{4}\s*', '', merchant)  # Remove leading numbers
        
        return merchant[:255]  # Limit length
    
    def normalize_boolean(self, value: Union[str, bool, int]) -> bool:
        """Normalize boolean values from CSV"""
        if pd.isna(value):
            return False
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        if isinstance(value, str):
            value = value.strip().lower()
            return value in ['true', '1', 'yes', 'y', 't']
        
        return False
    
    def map_transaction_type(self, is_income: bool, is_expense: bool, amount: Decimal) -> str:
        """Determine transaction type based on flags and amount"""
        if is_income:
            return "income"
        elif is_expense:
            return "expense"
        else:
            # Fallback to amount-based detection
            if amount > 0:
                return "income"
            elif amount < 0:
                return "expense"
            else:
                return "transfer"
    
    def generate_hash(self, user_id: str, date: datetime, amount: Decimal, merchant: str, memo: str = "") -> str:
        """Generate hash for deduplication"""
        content = f"{user_id}_{date.strftime('%Y-%m-%d')}_{amount}_{merchant}_{memo}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def process_transactions(self, df: pd.DataFrame, user_id: str, account_id: str = None) -> List[Dict]:
        """Process DataFrame into transaction dictionaries"""
        transactions = []
        batch_id = str(uuid.uuid4())
        
        for index, row in df.iterrows():
            try:
                # Extract and normalize core data
                date_val = row.get('Date', '')
                amount_val = row.get('Amount', 0)
                merchant_val = row.get('Merchant', '')
                message_val = row.get('Message', '')
                full_desc_val = row.get('Full_Description', '')
                
                # Parse values
                date = self.normalize_date(date_val)
                amount = self.normalize_amount(amount_val)
                merchant = self.normalize_merchant(merchant_val)
                
                if not date or amount is None:
                    self.warnings.append(f"Row {index + 1}: Missing date or amount")
                    continue
                
                # Extract additional fields
                main_category = str(row.get('Main_Category', '')).strip()
                category = str(row.get('Category', '')).strip() 
                subcategory = str(row.get('Subcategory', '')).strip()
                account = str(row.get('Account', '')).strip()
                owner = str(row.get('Owner', '')).strip()
                account_type = str(row.get('Account_Type', '')).strip()
                
                # Boolean fields
                is_expense = self.normalize_boolean(row.get('Is_Expense', False))
                is_income = self.normalize_boolean(row.get('Is_Income', False))
                
                # Determine transaction type
                transaction_type = self.map_transaction_type(is_income, is_expense, amount)
                
                # Create memo from available text fields
                memo_parts = []
                if message_val and str(message_val).strip():
                    memo_parts.append(str(message_val).strip())
                if full_desc_val and str(full_desc_val).strip() and str(full_desc_val).strip() != str(message_val).strip():
                    memo_parts.append(str(full_desc_val).strip())
                memo = " | ".join(memo_parts)[:500]  # Limit length
                
                # Generate deduplication hash
                hash_dedupe = self.generate_hash(user_id, date, amount, merchant, memo)
                
                # Build transaction object
                transaction = {
                    'user_id': user_id,
                    'account_id': account_id,
                    'posted_at': date,
                    'amount': amount,
                    'currency': 'USD',  # Default, could be detected from data
                    'merchant': merchant,
                    'memo': memo,
                    'import_batch_id': batch_id,
                    'hash_dedupe': hash_dedupe,
                    'source_category': 'imported',
                    
                    # Extended fields from CSV
                    'transaction_type': transaction_type,
                    'main_category': main_category,
                    'csv_category': category,
                    'csv_subcategory': subcategory,
                    'csv_account': account,
                    'owner': owner,
                    'csv_account_type': account_type,
                    'is_expense': is_expense,
                    'is_income': is_income,
                    'year': int(row.get('Year', date.year)) if pd.notna(row.get('Year')) else date.year,
                    'month': int(row.get('Month', date.month)) if pd.notna(row.get('Month')) else date.month,
                    'year_month': str(row.get('Year_Month', f"{date.year}-{date.month:02d}")).strip(),
                    'weekday': str(row.get('Weekday', date.strftime('%A'))).strip(),
                    'transfer_pair_id': row.get('Transfer_Pair_ID', None) if pd.notna(row.get('Transfer_Pair_ID')) else None
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
                continue
        
        return transactions
    
    def get_processing_summary(self, total_rows: int, processed_transactions: List[Dict]) -> Dict:
        """Get summary of processing results"""
        # Analyze transaction types
        type_counts = {}
        category_counts = {}
        
        for trans in processed_transactions:
            trans_type = trans.get('transaction_type', 'unknown')
            type_counts[trans_type] = type_counts.get(trans_type, 0) + 1
            
            main_cat = trans.get('main_category', 'uncategorized')
            category_counts[main_cat] = category_counts.get(main_cat, 0) + 1
        
        return {
            "total_rows": total_rows,
            "processed_rows": len(processed_transactions),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "error_messages": self.errors,
            "warning_messages": self.warnings,
            "success_rate": len(processed_transactions) / total_rows if total_rows > 0 else 0,
            "transaction_types": type_counts,
            "category_distribution": category_counts,
            "date_range": {
                "earliest": min(t['posted_at'] for t in processed_transactions).isoformat() if processed_transactions else None,
                "latest": max(t['posted_at'] for t in processed_transactions).isoformat() if processed_transactions else None
            }
        }

def process_csv_upload(file_content: Union[str, bytes], filename: str, user_id: str, account_id: str = None) -> Tuple[List[Dict], Dict]:
    """Main function to process a CSV upload"""
    processor = CSVProcessor()
    
    try:
        # Parse CSV
        df = processor.parse_csv_file(file_content, filename)
        
        # Process transactions
        transactions = processor.process_transactions(df, user_id, account_id)
        
        # Get summary
        summary = processor.get_processing_summary(len(df), transactions)
        
        return transactions, summary
        
    except Exception as e:
        summary = {
            "total_rows": 0,
            "processed_rows": 0,
            "errors": 1,
            "warnings": 0,
            "error_messages": [str(e)],
            "warning_messages": [],
            "success_rate": 0,
            "transaction_types": {},
            "category_distribution": {},
            "date_range": {"earliest": None, "latest": None}
        }
        return [], summary