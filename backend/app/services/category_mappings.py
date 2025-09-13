"""
Category Mappings System for Smart Personal Finance Planner
Handles automatic categorization of transactions using various rule types
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class PatternType(Enum):
    """Types of categorization patterns"""
    KEYWORD = "keyword"           # Simple keyword matching
    REGEX = "regex"              # Regular expression matching
    MCC = "mcc"                  # Merchant Category Code
    MERCHANT_EXACT = "merchant_exact"  # Exact merchant name
    CSV_MAPPING = "csv_mapping"  # Map from CSV categories
    AMOUNT_RANGE = "amount_range"  # Amount-based rules
    COMPOSITE = "composite"      # Multiple conditions

@dataclass
class CategoryMapping:
    """Represents a single categorization rule"""
    id: str
    user_id: str
    pattern_type: PatternType
    pattern_value: str
    category_id: str
    priority: int = 0
    confidence: float = 1.0
    active: bool = True
    description: str = ""

@dataclass
class CategorizationResult:
    """Result of categorization attempt"""
    category_id: Optional[str] = None
    confidence: float = 0.0
    rule_id: Optional[str] = None
    rule_description: str = ""
    matched_text: str = ""

class CategoryMapper:
    """Main category mapping engine"""
    
    def __init__(self):
        self.mappings: List[CategoryMapping] = []
        self.compiled_regexes: Dict[str, re.Pattern] = {}
    
    def load_mappings(self, mappings: List[CategoryMapping]):
        """Load category mappings and compile regex patterns"""
        self.mappings = sorted(mappings, key=lambda x: x.priority, reverse=True)
        
        # Pre-compile regex patterns for performance
        self.compiled_regexes = {}
        for mapping in self.mappings:
            if mapping.pattern_type == PatternType.REGEX and mapping.active:
                try:
                    self.compiled_regexes[mapping.id] = re.compile(
                        mapping.pattern_value, 
                        re.IGNORECASE
                    )
                except re.error:
                    print(f"Warning: Invalid regex pattern in mapping {mapping.id}: {mapping.pattern_value}")
    
    def categorize_transaction(
        self, 
        merchant: str = "", 
        memo: str = "", 
        amount: float = 0.0,
        mcc: str = "",
        csv_category: str = "",
        csv_subcategory: str = "",
        main_category: str = ""
    ) -> CategorizationResult:
        """
        Attempt to categorize a transaction using loaded mappings
        Returns the highest priority/confidence match
        """
        
        # Normalize inputs
        merchant = (merchant or "").strip().lower()
        memo = (memo or "").strip().lower()
        mcc = (mcc or "").strip()
        csv_category = (csv_category or "").strip().lower()
        csv_subcategory = (csv_subcategory or "").strip().lower()
        main_category = (main_category or "").strip().lower()
        
        # Combined text for keyword searches
        combined_text = f"{merchant} {memo}".strip()
        
        best_result = CategorizationResult()
        
        # Process mappings in priority order
        for mapping in self.mappings:
            if not mapping.active:
                continue
                
            result = self._test_mapping(
                mapping, merchant, memo, amount, mcc, 
                csv_category, csv_subcategory, main_category, combined_text
            )
            
            # Keep the best result (highest confidence, then priority)
            if (result.category_id and 
                (result.confidence > best_result.confidence or
                 (result.confidence == best_result.confidence and mapping.priority > 0))):
                best_result = result
                best_result.rule_id = mapping.id
                best_result.rule_description = mapping.description or f"{mapping.pattern_type.value}: {mapping.pattern_value}"
        
        return best_result
    
    def _test_mapping(
        self,
        mapping: CategoryMapping,
        merchant: str,
        memo: str, 
        amount: float,
        mcc: str,
        csv_category: str,
        csv_subcategory: str,
        main_category: str,
        combined_text: str
    ) -> CategorizationResult:
        """Test a single mapping against transaction data"""
        
        pattern_value = mapping.pattern_value.lower()
        
        if mapping.pattern_type == PatternType.KEYWORD:
            return self._test_keyword(mapping, combined_text, pattern_value)
            
        elif mapping.pattern_type == PatternType.REGEX:
            return self._test_regex(mapping, combined_text)
            
        elif mapping.pattern_type == PatternType.MERCHANT_EXACT:
            return self._test_merchant_exact(mapping, merchant, pattern_value)
            
        elif mapping.pattern_type == PatternType.MCC:
            return self._test_mcc(mapping, mcc, pattern_value)
            
        elif mapping.pattern_type == PatternType.CSV_MAPPING:
            return self._test_csv_mapping(mapping, csv_category, csv_subcategory, main_category, pattern_value)
            
        elif mapping.pattern_type == PatternType.AMOUNT_RANGE:
            return self._test_amount_range(mapping, amount, pattern_value)
            
        elif mapping.pattern_type == PatternType.COMPOSITE:
            return self._test_composite(mapping, merchant, memo, amount, mcc, csv_category, csv_subcategory, main_category)
        
        return CategorizationResult()
    
    def _test_keyword(self, mapping: CategoryMapping, combined_text: str, pattern_value: str) -> CategorizationResult:
        """Test keyword pattern"""
        if pattern_value in combined_text:
            return CategorizationResult(
                category_id=mapping.category_id,
                confidence=mapping.confidence,
                matched_text=pattern_value
            )
        return CategorizationResult()
    
    def _test_regex(self, mapping: CategoryMapping, combined_text: str) -> CategorizationResult:
        """Test regex pattern"""
        if mapping.id in self.compiled_regexes:
            match = self.compiled_regexes[mapping.id].search(combined_text)
            if match:
                return CategorizationResult(
                    category_id=mapping.category_id,
                    confidence=mapping.confidence,
                    matched_text=match.group(0)
                )
        return CategorizationResult()
    
    def _test_merchant_exact(self, mapping: CategoryMapping, merchant: str, pattern_value: str) -> CategorizationResult:
        """Test exact merchant match"""
        if merchant == pattern_value:
            return CategorizationResult(
                category_id=mapping.category_id,
                confidence=mapping.confidence,
                matched_text=merchant
            )
        return CategorizationResult()
    
    def _test_mcc(self, mapping: CategoryMapping, mcc: str, pattern_value: str) -> CategorizationResult:
        """Test MCC (Merchant Category Code) match"""
        if mcc and mcc == pattern_value:
            return CategorizationResult(
                category_id=mapping.category_id,
                confidence=mapping.confidence,
                matched_text=mcc
            )
        return CategorizationResult()
    
    def _test_csv_mapping(
        self, 
        mapping: CategoryMapping, 
        csv_category: str, 
        csv_subcategory: str, 
        main_category: str, 
        pattern_value: str
    ) -> CategorizationResult:
        """Test CSV category mapping"""
        # pattern_value format: "csv_field:value" e.g., "category:restaurants" or "main_category:food"
        try:
            field, value = pattern_value.split(":", 1)
            value = value.strip().lower()
            
            if field == "category" and csv_category == value:
                return CategorizationResult(
                    category_id=mapping.category_id,
                    confidence=mapping.confidence,
                    matched_text=f"CSV Category: {csv_category}"
                )
            elif field == "subcategory" and csv_subcategory == value:
                return CategorizationResult(
                    category_id=mapping.category_id,
                    confidence=mapping.confidence,
                    matched_text=f"CSV Subcategory: {csv_subcategory}"
                )
            elif field == "main_category" and main_category == value:
                return CategorizationResult(
                    category_id=mapping.category_id,
                    confidence=mapping.confidence,
                    matched_text=f"CSV Main Category: {main_category}"
                )
        except ValueError:
            pass
        
        return CategorizationResult()
    
    def _test_amount_range(self, mapping: CategoryMapping, amount: float, pattern_value: str) -> CategorizationResult:
        """Test amount range pattern"""
        # pattern_value format: "min:max" e.g., "0:50" for amounts between 0 and 50
        try:
            if ":" in pattern_value:
                min_amount, max_amount = pattern_value.split(":", 1)
                min_amount = float(min_amount) if min_amount else float('-inf')
                max_amount = float(max_amount) if max_amount else float('inf')
                
                if min_amount <= abs(amount) <= max_amount:
                    return CategorizationResult(
                        category_id=mapping.category_id,
                        confidence=mapping.confidence * 0.7,  # Lower confidence for amount-only rules
                        matched_text=f"Amount: ${abs(amount):.2f}"
                    )
        except ValueError:
            pass
        
        return CategorizationResult()
    
    def _test_composite(
        self,
        mapping: CategoryMapping,
        merchant: str,
        memo: str,
        amount: float,
        mcc: str,
        csv_category: str,
        csv_subcategory: str,
        main_category: str
    ) -> CategorizationResult:
        """Test composite pattern (multiple conditions)"""
        # pattern_value format: JSON-like string with multiple conditions
        # e.g., '{"merchant_contains": "starbucks", "amount_range": "0:20"}'
        try:
            import json
            conditions = json.loads(mapping.pattern_value)
            matches = 0
            total_conditions = len(conditions)
            matched_parts = []
            
            for condition_type, condition_value in conditions.items():
                if condition_type == "merchant_contains" and condition_value.lower() in merchant:
                    matches += 1
                    matched_parts.append(f"merchant: {condition_value}")
                elif condition_type == "memo_contains" and condition_value.lower() in memo:
                    matches += 1
                    matched_parts.append(f"memo: {condition_value}")
                elif condition_type == "amount_range":
                    min_amt, max_amt = map(float, condition_value.split(":"))
                    if min_amt <= abs(amount) <= max_amt:
                        matches += 1
                        matched_parts.append(f"amount: ${abs(amount):.2f}")
                elif condition_type == "mcc" and mcc == condition_value:
                    matches += 1
                    matched_parts.append(f"MCC: {mcc}")
            
            # Require all conditions to match for composite rules
            if matches == total_conditions:
                return CategorizationResult(
                    category_id=mapping.category_id,
                    confidence=mapping.confidence,
                    matched_text="; ".join(matched_parts)
                )
                
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        return CategorizationResult()

# Predefined category mappings for common patterns
DEFAULT_MAPPINGS = [
    # Food & Dining
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "starbucks",
        "description": "Starbucks coffee purchases",
        "priority": 100
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "mcdonald",
        "description": "McDonald's fast food",
        "priority": 100
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "restaurant",
        "description": "General restaurant purchases",
        "priority": 50
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "grocery",
        "description": "Grocery store purchases",
        "priority": 80
    },
    
    # Transportation
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "uber",
        "description": "Uber rides",
        "priority": 100
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "lyft",
        "description": "Lyft rides",
        "priority": 100
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "gas station",
        "description": "Gas station purchases",
        "priority": 80
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "parking",
        "description": "Parking fees",
        "priority": 70
    },
    
    # Shopping
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "amazon",
        "description": "Amazon purchases",
        "priority": 90
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "target",
        "description": "Target store purchases",
        "priority": 90
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "walmart",
        "description": "Walmart purchases",
        "priority": 90
    },
    
    # Utilities & Services
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "electric",
        "description": "Electric utility payments",
        "priority": 80
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "internet",
        "description": "Internet service payments",
        "priority": 80
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "phone",
        "description": "Phone service payments",
        "priority": 80
    },
    
    # Entertainment & Subscriptions
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "netflix",
        "description": "Netflix subscription",
        "priority": 100
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "spotify",
        "description": "Spotify subscription",
        "priority": 100
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "subscription",
        "description": "General subscription services",
        "priority": 60
    },
    
    # Healthcare
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "pharmacy",
        "description": "Pharmacy purchases",
        "priority": 90
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "doctor",
        "description": "Medical appointments",
        "priority": 80
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "dental",
        "description": "Dental services",
        "priority": 80
    },
    
    # Financial Services
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "atm",
        "description": "ATM withdrawals",
        "priority": 90
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "transfer",
        "description": "Account transfers",
        "priority": 70
    },
    {
        "pattern_type": PatternType.KEYWORD,
        "pattern_value": "fee",
        "description": "Bank fees",
        "priority": 60
    }
]

def create_csv_category_mappings(csv_data: Dict[str, str], user_categories: Dict[str, str]) -> List[Dict]:
    """
    Create category mappings based on CSV data analysis
    
    Args:
        csv_data: Dictionary mapping CSV categories to counts
        user_categories: Dictionary mapping category names to IDs
    
    Returns:
        List of mapping dictionaries ready for database insertion
    """
    mappings = []
    
    # Create mappings for CSV main categories
    for csv_main_cat, count in csv_data.get('main_categories', {}).items():
        csv_main_lower = csv_main_cat.lower()
        
        # Try to find matching user category
        for user_cat_name, user_cat_id in user_categories.items():
            if csv_main_lower in user_cat_name.lower() or user_cat_name.lower() in csv_main_lower:
                mappings.append({
                    "pattern_type": PatternType.CSV_MAPPING,
                    "pattern_value": f"main_category:{csv_main_lower}",
                    "category_id": user_cat_id,
                    "priority": 90,
                    "confidence": 0.8,
                    "description": f"Map CSV main category '{csv_main_cat}' to {user_cat_name}"
                })
                break
    
    # Create mappings for CSV categories
    for csv_cat, count in csv_data.get('categories', {}).items():
        csv_cat_lower = csv_cat.lower()
        
        # Try to find matching user category
        for user_cat_name, user_cat_id in user_categories.items():
            if csv_cat_lower in user_cat_name.lower() or user_cat_name.lower() in csv_cat_lower:
                mappings.append({
                    "pattern_type": PatternType.CSV_MAPPING,
                    "pattern_value": f"category:{csv_cat_lower}",
                    "category_id": user_cat_id,
                    "priority": 95,
                    "confidence": 0.9,
                    "description": f"Map CSV category '{csv_cat}' to {user_cat_name}"
                })
                break
    
    # Create mappings for CSV subcategories
    for csv_subcat, count in csv_data.get('subcategories', {}).items():
        csv_subcat_lower = csv_subcat.lower()
        
        # Try to find matching user category
        for user_cat_name, user_cat_id in user_categories.items():
            if csv_subcat_lower in user_cat_name.lower() or user_cat_name.lower() in csv_subcat_lower:
                mappings.append({
                    "pattern_type": PatternType.CSV_MAPPING,
                    "pattern_value": f"subcategory:{csv_subcat_lower}",
                    "category_id": user_cat_id,
                    "priority": 100,  # Highest priority for most specific match
                    "confidence": 0.95,
                    "description": f"Map CSV subcategory '{csv_subcat}' to {user_cat_name}"
                })
                break
    
    return mappings

def analyze_transaction_patterns(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Analyze transaction patterns to suggest new categorization rules
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Analysis results with suggested mappings
    """
    merchant_patterns = {}
    amount_patterns = {}
    memo_keywords = {}
    
    for trans in transactions:
        merchant = (trans.get('merchant', '') or '').lower()
        memo = (trans.get('memo', '') or '').lower()
        amount = abs(trans.get('amount', 0))
        category = trans.get('category_id')
        
        # Analyze merchant patterns
        if merchant and category:
            if merchant not in merchant_patterns:
                merchant_patterns[merchant] = {}
            if category not in merchant_patterns[merchant]:
                merchant_patterns[merchant][category] = 0
            merchant_patterns[merchant][category] += 1
        
        # Analyze memo keywords
        if memo and category:
            words = re.findall(r'\b\w{3,}\b', memo)  # Words with 3+ characters
            for word in words:
                if word not in memo_keywords:
                    memo_keywords[word] = {}
                if category not in memo_keywords[word]:
                    memo_keywords[word][category] = 0
                memo_keywords[word][category] += 1
        
        # Analyze amount ranges
        amount_range = f"{int(amount//10)*10}-{int(amount//10)*10+9}"
        if category:
            if amount_range not in amount_patterns:
                amount_patterns[amount_range] = {}
            if category not in amount_patterns[amount_range]:
                amount_patterns[amount_range][category] = 0
            amount_patterns[amount_range][category] += 1
    
    # Find strong patterns (high frequency, single category)
    suggested_mappings = []
    
    # Merchant suggestions
    for merchant, categories in merchant_patterns.items():
        total_trans = sum(categories.values())
        if total_trans >= 3:  # At least 3 transactions
            most_common_cat = max(categories, key=categories.get)
            confidence = categories[most_common_cat] / total_trans
            
            if confidence >= 0.8:  # 80% consistency
                suggested_mappings.append({
                    "type": "merchant_exact",
                    "pattern": merchant,
                    "category_id": most_common_cat,
                    "confidence": confidence,
                    "frequency": total_trans,
                    "description": f"Merchant '{merchant}' → category (confidence: {confidence:.1%})"
                })
    
    # Keyword suggestions
    for keyword, categories in memo_keywords.items():
        total_trans = sum(categories.values())
        if total_trans >= 5:  # At least 5 transactions
            most_common_cat = max(categories, key=categories.get)
            confidence = categories[most_common_cat] / total_trans
            
            if confidence >= 0.7:  # 70% consistency for keywords
                suggested_mappings.append({
                    "type": "keyword",
                    "pattern": keyword,
                    "category_id": most_common_cat,
                    "confidence": confidence,
                    "frequency": total_trans,
                    "description": f"Keyword '{keyword}' → category (confidence: {confidence:.1%})"
                })
    
    return {
        "suggested_mappings": sorted(suggested_mappings, key=lambda x: x["confidence"], reverse=True),
        "merchant_analysis": merchant_patterns,
        "keyword_analysis": memo_keywords,
        "amount_analysis": amount_patterns
    }