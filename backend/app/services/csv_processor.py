import pandas as pd
import hashlib
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Tuple, Optional, Union, Any
import re
from io import StringIO, BytesIO
import logging
import numpy as np
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCSVProcessor:
    """
    Enhanced CSV processor specifically designed for financial transaction data
    Handles large files (7500+ rows) efficiently with robust error handling
    """
    
    # Expected column mappings for your 19-column format
    EXPECTED_COLUMNS = {
        'Date': 'date',
        'Amount': 'amount', 
        'Merchant': 'merchant',
        'Message': 'message',
        'Full_Description': 'full_description',
        'Main_Category': 'main_category',
        'Category': 'category',
        'Subcategory': 'subcategory',
        'Account': 'account',
        'Owner': 'owner',
        'Account_Type': 'account_type',
        'Amount_Abs': 'amount_abs',
        'Is_Expense': 'is_expense',
        'Is_Income': 'is_income',
        'Year': 'year',
        'Month': 'month',
        'Year_Month': 'year_month',
        'Weekday': 'weekday',
        'Transfer_Pair_ID': 'transfer_pair_id'
    }
    
    # Date formats to try (most common first for performance)
    DATE_FORMATS = [
        '%d %m %Y',           # 26 08 2020 (your format)
        '%Y-%m-%d',           # 2023-12-25
        '%m/%d/%Y',           # 12/25/2023
        '%d/%m/%Y',           # 25/12/2023
        '%Y/%m/%d',           # 2023/12/25
        '%m-%d-%Y',           # 12-25-2023
        '%d-%m-%Y',           # 25-12-2023
        '%Y-%m-%d %H:%M:%S',  # 2023-12-25 14:30:00
        '%m/%d/%Y %H:%M:%S',  # 12/25/2023 14:30:00
        '%d/%m/%Y %H:%M:%S',  # 25/12/2023 14:30:00
        '%Y/%m/%d %H:%M:%S',  # 2023/12/25 14:30:00
        '%b %d, %Y',          # Dec 25, 2023
        '%B %d, %Y',          # December 25, 2023
        '%d %b %Y',           # 25 Dec 2023
        '%d %B %Y'            # 25 December 2023
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'error_rows': 0,
            'duplicate_rows': 0,
            'success_rate': 0.0
        }
    
    def detect_file_encoding(self, file_content: bytes) -> str:
        """
        Detect file encoding with fallback options
        """
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                content = file_content.decode(encoding)
                logger.info(f"Successfully detected encoding: {encoding}")
                return content
            except UnicodeDecodeError:
                continue
        
        # Final fallback with error handling
        logger.warning("Could not detect encoding, using UTF-8 with error replacement")
        return file_content.decode('utf-8', errors='replace')
    
    def parse_csv_content(self, file_content: Union[str, bytes], filename: str) -> pd.DataFrame:
        """
        Parse CSV content with robust error handling and format detection
        """
        try:
            # Handle bytes content
            if isinstance(file_content, bytes):
                content = self.detect_file_encoding(file_content)
            else:
                content = file_content.strip()
            
            if not content:
                raise ValueError("File appears to be empty")
            
            logger.info(f"Processing file: {filename}")
            logger.info(f"Content preview: {content[:200]}...")
            
            # Try different parsing strategies
            parsing_strategies = [
                # Strategy 1: Standard comma-separated
                {'sep': ',', 'quotechar': '"', 'skipinitialspace': True},
                # Strategy 2: Semicolon separated (European format)
                {'sep': ';', 'quotechar': '"', 'skipinitialspace': True},
                # Strategy 3: Tab separated
                {'sep': '\t', 'quotechar': '"', 'skipinitialspace': True},
                # Strategy 4: Pipe separated
                {'sep': '|', 'quotechar': '"', 'skipinitialspace': True},
                # Strategy 5: Auto-detect with pandas
                {'sep': None, 'quotechar': '"', 'skipinitialspace': True},
            ]
            
            df = None
            successful_strategy = None
            
            for i, strategy in enumerate(parsing_strategies, 1):
                try:
                    logger.info(f"Trying parsing strategy {i}: {strategy}")
                    
                    df = pd.read_csv(
                        StringIO(content),
                        dtype=str,  # Read everything as string initially
                        na_values=['', 'NULL', 'null', 'N/A', 'n/a', 'NA', '#N/A', 'None'],
                        keep_default_na=False,
                        encoding=None,  # Already handled encoding
                        on_bad_lines='skip',  # Skip problematic lines
                        **strategy
                    )
                    
                    # Validate the parsed result
                    if len(df.columns) >= 10 and len(df) > 0:  # Should have at least 10 columns for financial data
                        successful_strategy = strategy
                        logger.info(f"Successfully parsed with strategy {i}")
                        logger.info(f"DataFrame shape: {df.shape}")
                        logger.info(f"Columns: {list(df.columns)}")
                        break
                        
                except Exception as e:
                    logger.debug(f"Strategy {i} failed: {str(e)}")
                    continue
            
            if df is None or len(df) == 0:
                raise ValueError(f"Could not parse CSV file with any strategy. Content preview: {content[:500]}")
            
            # Clean column names
            df.columns = [col.strip().replace('\n', '').replace('\r', '') for col in df.columns]
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            if len(df) == 0:
                raise ValueError("No valid data rows found after cleaning")
            
            logger.info(f"Final DataFrame: {len(df)} rows × {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            error_msg = f"CSV parsing failed for {filename}: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            raise ValueError(error_msg)
    
    def map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Map DataFrame columns to our expected column names with fuzzy matching
        """
        column_mapping = {}
        available_columns = list(df.columns)
        
        logger.info(f"Mapping columns from: {available_columns}")
        
        # Exact matches first (case-insensitive)
        for expected_col, internal_name in self.EXPECTED_COLUMNS.items():
            for actual_col in available_columns:
                if actual_col.lower() == expected_col.lower():
                    column_mapping[internal_name] = actual_col
                    logger.info(f"Exact match: {internal_name} ← {actual_col}")
                    break
        
        # Fuzzy matches for unmapped columns
        remaining_expected = set(self.EXPECTED_COLUMNS.values()) - set(column_mapping.keys())
        remaining_actual = set(available_columns) - set(column_mapping.values())
        
        for internal_name in remaining_expected:
            expected_col = next(k for k, v in self.EXPECTED_COLUMNS.items() if v == internal_name)
            
            # Try partial matching
            for actual_col in remaining_actual:
                actual_lower = actual_col.lower()
                expected_lower = expected_col.lower()
                
                # Check if either contains the other
                if (expected_lower in actual_lower or 
                    actual_lower in expected_lower or
                    self._fuzzy_match(expected_lower, actual_lower)):
                    
                    column_mapping[internal_name] = actual_col
                    logger.info(f"Fuzzy match: {internal_name} ← {actual_col}")
                    remaining_actual.discard(actual_col)
                    break
        
        # Log unmapped columns
        unmapped = remaining_expected
        if unmapped:
            logger.warning(f"Unmapped expected columns: {unmapped}")
        
        unused = remaining_actual
        if unused:
            logger.info(f"Unused CSV columns: {unused}")
        
        return column_mapping
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.6) -> bool:
        """Simple fuzzy matching for column names"""
        # Remove common separators and check similarity
        clean1 = re.sub(r'[_\-\s]', '', str1)
        clean2 = re.sub(r'[_\-\s]', '', str2)
        
        if len(clean1) == 0 or len(clean2) == 0:
            return False
        
        # Simple character overlap ratio
        overlap = len(set(clean1) & set(clean2))
        max_len = max(len(clean1), len(clean2))
        similarity = overlap / max_len
        
        return similarity >= threshold
    
    def normalize_date(self, date_value: Any) -> Optional[datetime]:
        """Enhanced date normalization with multiple format support"""
        if pd.isna(date_value) or date_value == '' or date_value is None:
            return None
        
        date_str = str(date_value).strip()
        
        # Handle Excel date serial numbers
        if date_str.replace('.', '').isdigit():
            try:
                excel_date = float(date_str)
                if 25000 <= excel_date <= 50000:  # Reasonable range for Excel dates
                    base_date = datetime(1900, 1, 1)
                    return base_date + pd.Timedelta(days=excel_date-2)
            except (ValueError, OverflowError):
                pass
        
        # Try each date format
        for fmt in self.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Validate reasonable date range
                if 1990 <= parsed_date.year <= 2030:
                    return parsed_date
            except ValueError:
                continue
        
        # Fallback to pandas parser with dayfirst=True for European dates
        try:
            parsed_date = pd.to_datetime(date_str, dayfirst=True)
            if pd.notna(parsed_date):
                dt = parsed_date.to_pydatetime()
                if 1990 <= dt.year <= 2030:
                    return dt
        except:
            pass
        
        self.warnings.append(f"Could not parse date: {date_str}")
        return None
    
    def normalize_amount(self, amount_value: Any) -> Optional[Decimal]:
        """Enhanced amount normalization"""
        if pd.isna(amount_value) or amount_value == '' or amount_value is None:
            return None
        
        # Handle numeric types directly
        if isinstance(amount_value, (int, float)):
            if np.isfinite(amount_value):
                return Decimal(str(amount_value))
            else:
                return None
        
        amount_str = str(amount_value).strip()
        if not amount_str:
            return None
        
        # Remove currency symbols and thousands separators
        amount_str = re.sub(r'[$€£¥₹\s]', '', amount_str)
        
        # Handle parentheses for negative amounts (accounting format)
        is_negative = False
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = amount_str[1:-1]
            is_negative = True
        
        # Handle explicit signs
        if amount_str.startswith(('-', '+')):
            if amount_str.startswith('-'):
                is_negative = True
            amount_str = amount_str[1:]
        
        # Handle decimal separators
        if '.' in amount_str and ',' in amount_str:
            # Determine which is the decimal separator
            last_dot = amount_str.rfind('.')
            last_comma = amount_str.rfind(',')
            
            if last_dot > last_comma:
                # Dot is decimal separator
                amount_str = amount_str.replace(',', '')
            else:
                # Comma is decimal separator
                amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str:
            # Check if comma is likely a decimal separator
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) <= 3:
                amount_str = amount_str.replace(',', '.')
            else:
                amount_str = amount_str.replace(',', '')
        
        try:
            result = Decimal(amount_str)
            return -result if is_negative else result
        except (InvalidOperation, ValueError):
            self.warnings.append(f"Could not parse amount: {amount_value}")
            return None
    
    def normalize_boolean(self, bool_value: Any) -> bool:
        """Enhanced boolean normalization"""
        if pd.isna(bool_value) or bool_value == '':
            return False
        
        if isinstance(bool_value, bool):
            return bool_value
        
        if isinstance(bool_value, (int, float)):
            return bool(bool_value)
        
        if isinstance(bool_value, str):
            value = bool_value.strip().lower()
            return value in {'true', '1', 'yes', 'y', 't', 'on', 'checked'}
        
        return False
    
    def generate_dedup_hash(self, user_id: str, row_data: Dict) -> str:
        """Generate consistent hash for deduplication"""
        # Use only date and amount for deduplication to avoid false duplicates
        date_str = row_data.get('date', '').strftime('%Y-%m-%d') if row_data.get('date') else ''
        amount_str = str(row_data.get('amount', '0'))
        
        content = f"{user_id}_{date_str}_{amount_str}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def process_dataframe(self, df: pd.DataFrame, user_id: str, account_id: str = None) -> List[Dict]:
        """Process the DataFrame into transaction dictionaries"""
        transactions = []
        batch_id = str(uuid.uuid4())
        
        # Map columns
        column_map = self.map_columns(df)
        logger.info(f"Column mapping: {column_map}")
        
        # Check for required columns
        required = ['date', 'amount']
        missing_required = [col for col in required if col not in column_map]
        
        if missing_required:
            raise ValueError(f"Missing required columns: {missing_required}")
        
        self.stats['total_rows'] = len(df)
        logger.info(f"Processing {len(df)} rows...")
        
        for index, row in df.iterrows():
            try:
                # Extract core data
                date_val = row.get(column_map.get('date', ''), None)
                amount_val = row.get(column_map.get('amount', ''), None)
                
                # Parse required fields
                date = self.normalize_date(date_val)
                amount = self.normalize_amount(amount_val)
                
                if not date:
                    self.warnings.append(f"Row {index + 1}: Invalid date: {date_val}")
                    self.stats['error_rows'] += 1
                    continue
                
                if amount is None:
                    self.warnings.append(f"Row {index + 1}: Invalid amount: {amount_val}")
                    self.stats['error_rows'] += 1
                    continue
                
                # Extract all other fields with safe access
                def safe_get(col_key: str, default='') -> str:
                    if col_key in column_map:
                        val = row.get(column_map[col_key], default)
                        return str(val).strip() if pd.notna(val) and val != '' else str(default)
                    return str(default)
                
                def safe_get_bool(col_key: str) -> bool:
                    if col_key in column_map:
                        val = row.get(column_map[col_key], False)
                        return self.normalize_boolean(val)
                    return False
                
                def safe_get_int(col_key: str, default: int = None) -> Optional[int]:
                    if col_key in column_map:
                        val = row.get(column_map[col_key], default)
                        if pd.notna(val) and val != '':
                            try:
                                return int(float(val))  # Handle "2023.0" -> 2023
                            except (ValueError, TypeError):
                                pass
                    return default
                
                # Build transaction object with all available fields
                transaction = {
                    'user_id': user_id,
                    'account_id': account_id,
                    'posted_at': date,
                    'amount': amount,
                    'currency': 'EUR',  # Default for European data
                    'merchant': safe_get('merchant'),
                    'memo': safe_get('message'),
                    'import_batch_id': batch_id,
                    'source_category': 'imported',
                    
                    # Enhanced fields from your CSV format
                    'full_description': safe_get('full_description'),
                    'main_category': safe_get('main_category'),
                    'csv_category': safe_get('category'),
                    'csv_subcategory': safe_get('subcategory'),
                    'csv_account': safe_get('account'),
                    'owner': safe_get('owner'),
                    'csv_account_type': safe_get('account_type'),
                    
                    # Pre-calculated fields
                    'amount_abs': self.normalize_amount(row.get(column_map.get('amount_abs', ''), amount)),
                    'is_expense': safe_get_bool('is_expense'),
                    'is_income': safe_get_bool('is_income'),
                    
                    # Date components
                    'year': safe_get_int('year', date.year),
                    'month': safe_get_int('month', date.month),
                    'year_month': safe_get('year_month') or f"{date.year}-{date.month:02d}",
                    'weekday': safe_get('weekday') or date.strftime('%A'),
                    
                    # Transfer linking
                    'transfer_pair_id': safe_get('transfer_pair_id') or None,
                    
                    # Determine transaction type
                    'transaction_type': self._determine_transaction_type(
                        safe_get_bool('is_income'),
                        safe_get_bool('is_expense'),
                        amount,
                        safe_get('merchant')
                    ),
                    
                    # Metadata
                    'confidence_score': None,  # Will be set by categorization
                    'review_needed': False,    # Will be determined by rules
                    'tags': None,
                    'notes': None
                }
                
                # Generate deduplication hash
                transaction['hash_dedupe'] = self.generate_dedup_hash(user_id, transaction)
                
                transactions.append(transaction)
                self.stats['processed_rows'] += 1
                
                # Progress logging for large files
                if (index + 1) % 1000 == 0:
                    logger.info(f"Processed {index + 1}/{len(df)} rows...")
                
            except Exception as e:
                error_msg = f"Row {index + 1}: {str(e)}"
                self.errors.append(error_msg)
                self.stats['error_rows'] += 1
                logger.debug(f"Error processing row {index + 1}: {e}")
                continue
        
        # Calculate success rate
        self.stats['success_rate'] = (
            self.stats['processed_rows'] / self.stats['total_rows'] 
            if self.stats['total_rows'] > 0 else 0
        )
        
        logger.info(f"Processing complete: {self.stats['processed_rows']}/{self.stats['total_rows']} rows successful ({self.stats['success_rate']:.1%})")
        
        return transactions
    
    def _determine_transaction_type(self, is_income: bool, is_expense: bool, amount: Decimal, merchant: str) -> str:
        """Determine transaction type using available data"""
        if is_income:
            return "income"
        elif is_expense:
            return "expense"
        
        # Fallback logic
        if amount is None:
            return "unknown"
        
        # Check for transfer keywords
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
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Generate comprehensive processing summary"""
        return {
            'total_rows': self.stats['total_rows'],
            'processed_rows': self.stats['processed_rows'],
            'error_rows': self.stats['error_rows'],
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'error_messages': self.errors[:10],  # Limit to first 10
            'warning_messages': self.warnings[:10],  # Limit to first 10
            'success_rate': self.stats['success_rate'],
            'column_mappings': {},  # Will be filled by calling code
            'processing_stats': self.stats
        }


def process_csv_upload(
    file_content: Union[str, bytes], 
    filename: str, 
    user_id: str, 
    account_id: str = None
) -> Tuple[List[Dict], Dict]:
    """
    Main entry point for CSV processing
    
    Args:
        file_content: Raw file content (string or bytes)
        filename: Original filename
        user_id: User identifier
        account_id: Account identifier (optional)
    
    Returns:
        Tuple of (transactions_list, summary_dict)
    """
    processor = EnhancedCSVProcessor()
    
    try:
        logger.info(f"Starting enhanced CSV processing for: {filename}")
        logger.info(f"File size: {len(file_content)} {'bytes' if isinstance(file_content, bytes) else 'characters'}")
        
        # Step 1: Parse CSV
        df = processor.parse_csv_content(file_content, filename)
        logger.info(f"CSV parsed: {len(df)} rows × {len(df.columns)} columns")
        
        # Step 2: Process transactions
        transactions = processor.process_dataframe(df, user_id, account_id)
        logger.info(f"Transactions processed: {len(transactions)} created")
        
        # Step 3: Generate summary
        summary = processor.get_processing_summary()
        
        # Add additional summary data
        if transactions:
            summary.update({
                'date_range': {
                    'earliest': min(t['posted_at'] for t in transactions).isoformat(),
                    'latest': max(t['posted_at'] for t in transactions).isoformat()
                },
                'transaction_types': {
                    t_type: len([t for t in transactions if t['transaction_type'] == t_type])
                    for t_type in set(t['transaction_type'] for t in transactions)
                },
                'category_distribution': {
                    cat: len([t for t in transactions if t['main_category'] == cat])
                    for cat in set(t['main_category'] for t in transactions if t['main_category'])
                }
            })
        else:
            summary.update({
                'date_range': {'earliest': None, 'latest': None},
                'transaction_types': {},
                'category_distribution': {}
            })
        
        logger.info(f"Processing completed successfully!")
        return transactions, summary
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        
        error_summary = {
            'total_rows': 0,
            'processed_rows': 0,
            'error_rows': 0,
            'errors': 1,
            'warnings': len(processor.warnings),
            'error_messages': [f"Processing failed: {str(e)}"],
            'warning_messages': processor.warnings,
            'success_rate': 0.0,
            'transaction_types': {},
            'category_distribution': {},
            'date_range': {'earliest': None, 'latest': None},
            'processing_stats': processor.stats
        }
        
        return [], error_summary