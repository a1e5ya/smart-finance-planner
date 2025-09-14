import pandas as pd
import hashlib
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Tuple, Optional, Union
import re
from io import StringIO, BytesIO
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVProcessor:
    """Enhanced CSV processor with better error handling and flexible column mapping"""
    
    # Expected columns with multiple possible names (case-insensitive)
    COLUMN_MAPPINGS = {
        "date": ["Date", "date", "DATE", "Transaction Date", "Posted Date", "transaction_date", "posted_date"],
        "amount": ["Amount", "amount", "AMOUNT", "Transaction Amount", "transaction_amount"], 
        "merchant": ["Merchant", "merchant", "MERCHANT", "Description", "description", "DESCRIPTION", "Payee", "payee"],
        "message": ["Message", "message", "MESSAGE", "Memo", "memo", "MEMO", "Note", "note"],
        "full_description": ["Full_Description", "full_description", "FULL_DESCRIPTION", "Details", "details"],
        "main_category": ["Main_Category", "main_category", "MAIN_CATEGORY", "Category", "Primary Category"],
        "category": ["Category", "category", "CATEGORY", "Sub Category", "SubCategory", "sub_category"],
        "subcategory": ["Subcategory", "subcategory", "SUBCATEGORY", "Sub_Category", "subCategory"],
        "account": ["Account", "account", "ACCOUNT", "Account Name", "account_name"],
        "owner": ["Owner", "owner", "OWNER", "Account Owner", "account_owner"],
        "account_type": ["Account_Type", "account_type", "ACCOUNT_TYPE", "Account Type", "Type"],
        "amount_abs": ["Amount_Abs", "amount_abs", "AMOUNT_ABS", "Absolute Amount", "abs_amount"],
        "is_expense": ["Is_Expense", "is_expense", "IS_EXPENSE", "Expense", "expense"],
        "is_income": ["Is_Income", "is_income", "IS_INCOME", "Income", "income"],
        "year": ["Year", "year", "YEAR"],
        "month": ["Month", "month", "MONTH"],
        "year_month": ["Year_Month", "year_month", "YEAR_MONTH", "YearMonth", "year-month"],
        "weekday": ["Weekday", "weekday", "WEEKDAY", "Day of Week", "day_of_week", "DayOfWeek"],
        "transfer_pair_id": ["Transfer_Pair_ID", "transfer_pair_id", "TRANSFER_PAIR_ID", "Transfer ID", "transfer_id"]
    }
    
    # Date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d", "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y", "%m/%d/%y", "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y", "%d/%m/%y", "%d/%m/%Y %H:%M:%S",
        "%Y/%m/%d", "%Y/%m/%d %H:%M:%S",
        "%m-%d-%Y", "%m-%d-%y",
        "%d-%m-%Y", "%d-%m-%y",
        "%b %d, %Y", "%B %d, %Y",
        "%d %b %Y", "%d %B %Y"
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.column_map = {}
        
    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect which columns in the DataFrame match our expected columns"""
        column_map = {}
        available_columns = [col.strip() for col in df.columns]
        
        logger.info(f"Available columns: {available_columns}")
        
        for expected_key, possible_names in self.COLUMN_MAPPINGS.items():
            found_column = None
            
            # Try exact matches first (case-insensitive)
            for possible_name in possible_names:
                for actual_column in available_columns:
                    if actual_column.lower() == possible_name.lower():
                        found_column = actual_column
                        break
                if found_column:
                    break
            
            # If no exact match, try partial matches
            if not found_column:
                for possible_name in possible_names:
                    for actual_column in available_columns:
                        if possible_name.lower() in actual_column.lower() or actual_column.lower() in possible_name.lower():
                            found_column = actual_column
                            break
                    if found_column:
                        break
            
            if found_column:
                column_map[expected_key] = found_column
                logger.info(f"Mapped {expected_key} -> {found_column}")
        
        # Check for required columns
        required_columns = ['date', 'amount']
        missing_required = [col for col in required_columns if col not in column_map]
        
        if missing_required:
            # Try common alternative patterns
            if 'date' not in column_map:
                date_candidates = [col for col in available_columns if 
                                 any(word in col.lower() for word in ['date', 'time', 'posted', 'transaction'])]
                if date_candidates:
                    column_map['date'] = date_candidates[0]
                    logger.info(f"Found date candidate: {date_candidates[0]}")
                    missing_required.remove('date')
            
            if 'amount' not in column_map:
                amount_candidates = [col for col in available_columns if 
                                   any(word in col.lower() for word in ['amount', 'value', 'total', 'sum'])]
                if amount_candidates:
                    column_map['amount'] = amount_candidates[0]
                    logger.info(f"Found amount candidate: {amount_candidates[0]}")
                    missing_required.remove('amount')
        
        if missing_required:
            raise ValueError(f"Missing required columns: {missing_required}. Available: {available_columns}")
        
        self.column_map = column_map
        return column_map
    
    def parse_csv_file(self, file_content: Union[str, bytes], filename: str) -> pd.DataFrame:
        """Parse CSV file content into a pandas DataFrame with flexible parsing"""
        try:
            # Handle bytes or string content
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8-sig')  # Handle BOM
            
            # Clean the content
            file_content = file_content.strip()
            
            if not file_content:
                raise ValueError("File is empty")
            
            # Try different separators and encodings
            separators = [',', ';', '\t', '|']
            df = None
            
            for sep in separators:
                try:
                    # Try with different quote characters and escaping
                    for quotechar in ['"', "'"]:
                        try:
                            df = pd.read_csv(
                                StringIO(file_content), 
                                separator=sep,
                                quotechar=quotechar,
                                escapechar='\\',
                                skipinitialspace=True,
                                dtype=str,  # Read everything as string initially
                                na_values=['', 'NULL', 'null', 'N/A', 'n/a', 'NA', '#N/A'],
                                keep_default_na=False
                            )
                            if len(df.columns) > 1 and len(df) > 0:
                                logger.info(f"Successfully parsed with separator '{sep}' and quotechar '{quotechar}'")
                                break
                        except Exception as e:
                            continue
                    if df is not None and len(df.columns) > 1:
                        break
                except Exception as e:
                    logger.debug(f"Failed with separator '{sep}': {e}")
                    continue
            
            if df is None or len(df.columns) <= 1 or len(df) == 0:
                raise ValueError(f"Could not parse CSV file. Tried separators: {separators}")
            
            # Clean column names - remove extra whitespace and special characters
            df.columns = [col.strip().replace('\n', '').replace('\r', '') for col in df.columns]
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Remove rows where all important fields are empty
            if len(df) == 0:
                raise ValueError("No data rows found after cleaning")
            
            logger.info(f"Parsed CSV: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            self.errors.append(f"Failed to parse CSV: {str(e)}")
            logger.error(f"CSV parsing failed: {str(e)}")
            raise ValueError(f"CSV parsing failed: {str(e)}")
    
    def normalize_date(self, date_str: str) -> Optional[datetime]:
        """Normalize date string to datetime object"""
        if pd.isna(date_str) or not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Handle Excel date serial numbers
        try:
            if date_str.isdigit() and len(date_str) == 5:  # Excel date serial
                excel_date = int(date_str)
                if 25000 < excel_date < 50000:  # Reasonable range for dates
                    return datetime(1900, 1, 1) + pd.Timedelta(days=excel_date-2)
        except:
            pass
        
        for fmt in self.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Validate date is reasonable (between 1900 and 2030)
                if 1900 <= parsed_date.year <= 2030:
                    return parsed_date
            except ValueError:
                continue
        
        # Try pandas date parser as fallback
        try:
            parsed_date = pd.to_datetime(date_str, infer_datetime_format=True)
            if pd.notna(parsed_date):
                return parsed_date.to_pydatetime()
        except:
            pass
        
        self.warnings.append(f"Could not parse date: {date_str}")
        return None
    
    def normalize_amount(self, amount_str: Union[str, int, float]) -> Optional[Decimal]:
        """Normalize amount to Decimal with enhanced parsing"""
        if pd.isna(amount_str) or amount_str == '' or amount_str is None:
            return None
        
        # Convert to string and clean
        amount_str = str(amount_str).strip()
        
        if not amount_str:
            return None
        
        # Remove currency symbols, spaces, and common formatting
        amount_str = re.sub(r'[$€£¥₹,\s]', '', amount_str)
        
        # Handle parentheses as negative (accounting format)
        is_negative = False
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = amount_str[1:-1]
            is_negative = True
        
        # Handle negative signs
        if amount_str.startswith('-'):
            is_negative = True
            amount_str = amount_str[1:]
        elif amount_str.startswith('+'):
            amount_str = amount_str[1:]
        
        # Handle different decimal separators
        # If there are multiple periods or commas, assume the last one is decimal
        if '.' in amount_str and ',' in amount_str:
            last_period = amount_str.rfind('.')
            last_comma = amount_str.rfind(',')
            if last_period > last_comma:
                # Period is decimal separator
                amount_str = amount_str.replace(',', '')
            else:
                # Comma is decimal separator
                amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str:
            # Check if comma is likely decimal separator (has 2 digits after)
            comma_parts = amount_str.split(',')
            if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                amount_str = amount_str.replace(',', '.')
            else:
                amount_str = amount_str.replace(',', '')
        
        try:
            result = Decimal(amount_str)
            if is_negative:
                result = -result
            return result
        except (InvalidOperation, ValueError):
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
        merchant = re.sub(r'^\d{4,}\s*', '', merchant)  # Remove leading numbers (often IDs)
        merchant = re.sub(r'#\d+$', '', merchant)  # Remove trailing reference numbers
        
        return merchant[:255]  # Limit length
    
    def normalize_boolean(self, value: Union[str, bool, int, float]) -> bool:
        """Normalize boolean values from CSV"""
        if pd.isna(value):
            return False
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        if isinstance(value, str):
            value = value.strip().lower()
            return value in ['true', '1', 'yes', 'y', 't', 'on']
        
        return False
    
    def map_transaction_type(self, is_income: bool, is_expense: bool, amount: Decimal, merchant: str = "") -> str:
        """Determine transaction type based on flags and amount"""
        if is_income:
            return "income"
        elif is_expense:
            return "expense"
        else:
            # Enhanced logic based on amount and merchant
            if amount is None:
                return "unknown"
            
            # Check for transfer keywords in merchant
            transfer_keywords = ['transfer', 'xfer', 'payment to', 'payment from', 'internal', 'between accounts']
            if any(keyword in merchant.lower() for keyword in transfer_keywords):
                return "transfer"
            
            # Amount-based detection
            if amount > 0:
                return "income"
            elif amount < 0:
                return "expense"
            else:
                return "transfer"
    
    def generate_hash(self, user_id: str, date: datetime, amount: Decimal, merchant: str, memo: str = "") -> str:
        """Generate hash for deduplication"""
        # Create a more robust hash that handles slight variations
        amount_str = str(abs(float(amount))) if amount else "0"
        date_str = date.strftime('%Y-%m-%d') if date else ""
        merchant_clean = re.sub(r'[^\w\s]', '', merchant.lower()) if merchant else ""
        memo_clean = re.sub(r'[^\w\s]', '', memo.lower())[:50] if memo else ""  # Truncate memo
        
        content = f"{user_id}_{date_str}_{amount_str}_{merchant_clean}_{memo_clean}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_column_value(self, row: pd.Series, column_key: str, default="") -> str:
        """Safely get column value with fallback"""
        if column_key in self.column_map:
            column_name = self.column_map[column_key]
            value = row.get(column_name, default)
            return str(value).strip() if pd.notna(value) else str(default)
        return str(default)
    
    def process_transactions(self, df: pd.DataFrame, user_id: str, account_id: str = None) -> List[Dict]:
        """Process DataFrame into transaction dictionaries"""
        transactions = []
        batch_id = str(uuid.uuid4())
        
        # Detect column mappings
        try:
            self.detect_columns(df)
        except ValueError as e:
            self.errors.append(str(e))
            return []
        
        logger.info(f"Processing {len(df)} rows with column mappings: {self.column_map}")
        
        for index, row in df.iterrows():
            try:
                # Extract and normalize core data
                date_val = self.get_column_value(row, 'date')
                amount_val = self.get_column_value(row, 'amount', 0)
                merchant_val = self.get_column_value(row, 'merchant')
                
                # Parse values
                date = self.normalize_date(date_val)
                amount = self.normalize_amount(amount_val)
                merchant = self.normalize_merchant(merchant_val)
                
                if not date:
                    self.warnings.append(f"Row {index + 1}: Invalid or missing date: {date_val}")
                    continue
                
                if amount is None:
                    self.warnings.append(f"Row {index + 1}: Invalid or missing amount: {amount_val}")
                    continue
                
                # Extract additional fields with safe access
                message_val = self.get_column_value(row, 'message')
                full_desc_val = self.get_column_value(row, 'full_description')
                main_category = self.get_column_value(row, 'main_category')
                category = self.get_column_value(row, 'category')
                subcategory = self.get_column_value(row, 'subcategory')
                account = self.get_column_value(row, 'account')
                owner = self.get_column_value(row, 'owner')
                account_type = self.get_column_value(row, 'account_type')
                
                # Boolean fields
                is_expense = self.normalize_boolean(self.get_column_value(row, 'is_expense', False))
                is_income = self.normalize_boolean(self.get_column_value(row, 'is_income', False))
                
                # Determine transaction type
                transaction_type = self.map_transaction_type(is_income, is_expense, amount, merchant)
                
                # Create memo from available text fields
                memo_parts = []
                if message_val:
                    memo_parts.append(message_val)
                if full_desc_val and full_desc_val != message_val:
                    memo_parts.append(full_desc_val)
                memo = " | ".join(memo_parts)[:500]  # Limit length
                
                # Generate deduplication hash
                hash_dedupe = self.generate_hash(user_id, date, amount, merchant, memo)
                
                # Extract year/month info
                year_val = self.get_column_value(row, 'year')
                month_val = self.get_column_value(row, 'month')
                year_month_val = self.get_column_value(row, 'year_month')
                weekday_val = self.get_column_value(row, 'weekday')
                
                # Validate or calculate year/month
                year = int(year_val) if year_val.isdigit() else date.year
                month = int(month_val) if month_val.isdigit() and 1 <= int(month_val) <= 12 else date.month
                year_month = year_month_val if year_month_val else f"{year}-{month:02d}"
                weekday = weekday_val if weekday_val else date.strftime('%A')
                
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
                    'year': year,
                    'month': month,
                    'year_month': year_month,
                    'weekday': weekday,
                    'transfer_pair_id': self.get_column_value(row, 'transfer_pair_id') or None
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
                logger.error(f"Error processing row {index + 1}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(transactions)} transactions from {len(df)} rows")
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
            if main_cat:
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
            "column_mappings": self.column_map,
            "date_range": {
                "earliest": min(t['posted_at'] for t in processed_transactions).isoformat() if processed_transactions else None,
                "latest": max(t['posted_at'] for t in processed_transactions).isoformat() if processed_transactions else None
            }
        }

def process_csv_upload(file_content: Union[str, bytes], filename: str, user_id: str, account_id: str = None) -> Tuple[List[Dict], Dict]:
    """Main function to process a CSV upload with enhanced error handling"""
    processor = CSVProcessor()
    
    try:
        logger.info(f"Starting CSV processing for file: {filename}")
        
        # Parse CSV
        df = processor.parse_csv_file(file_content, filename)
        logger.info(f"CSV parsed successfully: {len(df)} rows, {len(df.columns)} columns")
        
        # Process transactions
        transactions = processor.process_transactions(df, user_id, account_id)
        logger.info(f"Processed {len(transactions)} transactions")
        
        # Get summary
        summary = processor.get_processing_summary(len(df), transactions)
        
        return transactions, summary
        
    except Exception as e:
        logger.error(f"CSV processing failed: {e}")
        summary = {
            "total_rows": 0,
            "processed_rows": 0,
            "errors": 1,
            "warnings": 0,
            "error_messages": [f"Processing failed: {str(e)}"],
            "warning_messages": processor.warnings,
            "success_rate": 0,
            "transaction_types": {},
            "category_distribution": {},
            "column_mappings": {},
            "date_range": {"earliest": None, "latest": None}
        }
        return [], summary