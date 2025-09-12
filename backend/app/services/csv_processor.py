import pandas as pd
import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Tuple, Optional, Union
import re
from io import StringIO, BytesIO

class CSVProcessor:
    """Process CSV files from various banks and financial institutions"""
    
    # Common column mappings for different banks
    COLUMN_MAPPINGS = {
        "chase": {
            "date": ["Transaction Date", "Date"],
            "amount": ["Amount"],
            "merchant": ["Description"],
            "memo": ["Details", "Memo"],
            "account": ["Account"]
        },
        "bank_of_america": {
            "date": ["Date"],
            "amount": ["Amount"],
            "merchant": ["Description"],
            "memo": ["Details"],
            "account": ["Account"]
        },
        "wells_fargo": {
            "date": ["Date"],
            "amount": ["Amount"],
            "merchant": ["Description"],
            "memo": ["Details"],
            "account": ["Account"]
        },
        "generic": {
            "date": ["date", "transaction_date", "posted_date", "Date", "Transaction Date"],
            "amount": ["amount", "Amount", "Debit", "Credit"],
            "merchant": ["description", "merchant", "Description", "Merchant", "Payee"],
            "memo": ["memo", "details", "Memo", "Details", "Notes"],
            "account": ["account", "Account", "Account Name"]
        }
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
    
    def detect_bank_format(self, df: pd.DataFrame) -> str:
        """Detect the bank format based on column names"""
        columns = [col.lower().strip() for col in df.columns]
        
        # Check for specific bank patterns
        if any("chase" in col for col in columns):
            return "chase"
        elif any("bank of america" in col for col in columns):
            return "bank_of_america"
        elif any("wells fargo" in col for col in columns):
            return "wells_fargo"
        else:
            return "generic"
    
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
            
            # Clean column names
            df.columns = [col.strip() for col in df.columns]
            
            # Remove empty rows
            df = df.dropna(how='all')
            
            return df
            
        except Exception as e:
            self.errors.append(f"Failed to parse CSV: {str(e)}")
            raise ValueError(f"CSV parsing failed: {str(e)}")
    
    def map_columns(self, df: pd.DataFrame, bank_format: str) -> Dict[str, str]:
        """Map CSV columns to our standard field names"""
        mappings = self.COLUMN_MAPPINGS.get(bank_format, self.COLUMN_MAPPINGS["generic"])
        result = {}
        
        df_columns = [col.strip() for col in df.columns]
        
        for field, possible_names in mappings.items():
            mapped_column = None
            
            # Try exact matches first
            for col_name in possible_names:
                if col_name in df_columns:
                    mapped_column = col_name
                    break
            
            # Try case-insensitive partial matches
            if not mapped_column:
                for col_name in possible_names:
                    for df_col in df_columns:
                        if col_name.lower() in df_col.lower():
                            mapped_column = df_col
                            break
                    if mapped_column:
                        break
            
            if mapped_column:
                result[field] = mapped_column
            else:
                self.warnings.append(f"Could not find column for {field}")
        
        return result
    
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
    
    def normalize_amount(self, amount_str: str) -> Optional[Decimal]:
        """Normalize amount string to Decimal"""
        if pd.isna(amount_str) or not amount_str:
            return None
        
        # Convert to string and clean
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and spaces
        amount_str = re.sub(r'[$€£¥,\s]', '', amount_str)
        
        # Handle parentheses as negative (common in accounting)
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = '-' + amount_str[1:-1]
        
        try:
            return Decimal(amount_str)
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
    
    def generate_hash(self, user_id: str, date: datetime, amount: Decimal, merchant: str, memo: str = "") -> str:
        """Generate hash for deduplication"""
        content = f"{user_id}_{date.strftime('%Y-%m-%d')}_{amount}_{merchant}_{memo}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def process_transactions(self, df: pd.DataFrame, user_id: str, account_id: str = None) -> List[Dict]:
        """Process DataFrame into transaction dictionaries"""
        bank_format = self.detect_bank_format(df)
        column_map = self.map_columns(df, bank_format)
        
        if not column_map.get('date') or not column_map.get('amount'):
            raise ValueError("Required columns (date, amount) not found in CSV")
        
        transactions = []
        batch_id = str(uuid.uuid4())
        
        for index, row in df.iterrows():
            try:
                # Extract and normalize data
                date = self.normalize_date(row.get(column_map.get('date')))
                amount = self.normalize_amount(row.get(column_map.get('amount')))
                merchant = self.normalize_merchant(row.get(column_map.get('merchant', ''), ''))
                memo = str(row.get(column_map.get('memo', ''), '')).strip()[:500]
                
                if not date or amount is None:
                    self.warnings.append(f"Row {index + 1}: Missing date or amount")
                    continue
                
                # Generate deduplication hash
                hash_dedupe = self.generate_hash(user_id, date, amount, merchant, memo)
                
                transaction = {
                    'user_id': user_id,
                    'account_id': account_id,
                    'posted_at': date,
                    'amount': amount,
                    'currency': 'USD',  # Default, could be detected
                    'merchant': merchant,
                    'memo': memo,
                    'import_batch_id': batch_id,
                    'hash_dedupe': hash_dedupe,
                    'source_category': 'user'
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
                continue
        
        return transactions
    
    def get_processing_summary(self, total_rows: int, processed_transactions: List[Dict]) -> Dict:
        """Get summary of processing results"""
        return {
            "total_rows": total_rows,
            "processed_rows": len(processed_transactions),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "error_messages": self.errors,
            "warning_messages": self.warnings,
            "success_rate": len(processed_transactions) / total_rows if total_rows > 0 else 0
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
            "success_rate": 0
        }
        return [], summary