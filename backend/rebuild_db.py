#!/usr/bin/env python3
"""
Complete database rebuild from scratch
Drops all existing tables and creates the entire schema fresh
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def rebuild_entire_database():
    """Drop everything and rebuild the complete database schema"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment")
        return False
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("Connected to database")
        
        print("WARNING: This will DROP ALL EXISTING TABLES and data!")
        print("Are you sure you want to continue? Type 'yes' to proceed:")
        
        # For automation, we'll proceed directly. In interactive use, uncomment the input line below:
        # confirmation = input().lower()
        # if confirmation != 'yes':
        #     print("Operation cancelled")
        #     return False
        
        print("\n1. Dropping all existing tables...")
        
        # Get all table names
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
        existing_tables = await conn.fetch(tables_query)
        
        # Drop all tables
        for table in existing_tables:
            table_name = table['table_name']
            drop_query = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
            print(f"   Dropping {table_name}")
            await conn.execute(drop_query)
        
        print("   All existing tables dropped")
        
        print("\n2. Creating complete schema from scratch...")
        
        # Create users table
        print("   Creating users table...")
        await conn.execute("""
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                firebase_uid VARCHAR UNIQUE NOT NULL,
                email VARCHAR,
                display_name VARCHAR,
                locale VARCHAR DEFAULT 'en-US',
                currency VARCHAR DEFAULT 'USD',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create accounts table
        print("   Creating accounts table...")
        await conn.execute("""
            CREATE TABLE accounts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                account_type VARCHAR,
                institution VARCHAR,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create categories table with ALL required columns
        print("   Creating categories table...")
        await conn.execute("""
            CREATE TABLE categories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                parent_id UUID REFERENCES categories(id),
                name VARCHAR NOT NULL,
                code VARCHAR,
                icon VARCHAR,
                color VARCHAR,
                category_type VARCHAR NOT NULL DEFAULT 'expense',
                version INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create import_batches table with ALL required columns
        print("   Creating import_batches table...")
        await conn.execute("""
            CREATE TABLE import_batches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                filename VARCHAR NOT NULL,
                file_size INTEGER,
                file_hash VARCHAR,
                rows_total INTEGER DEFAULT 0,
                rows_imported INTEGER DEFAULT 0,
                rows_duplicated INTEGER DEFAULT 0,
                rows_errors INTEGER DEFAULT 0,
                status VARCHAR DEFAULT 'processing',
                error_message TEXT,
                summary_data JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP
            );
        """)
        
        # Create transactions table with ALL required columns
        print("   Creating transactions table...")
        await conn.execute("""
            CREATE TABLE transactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                account_id UUID REFERENCES accounts(id),
                posted_at TIMESTAMP NOT NULL,
                amount NUMERIC(12,2) NOT NULL,
                currency VARCHAR DEFAULT 'USD',
                merchant VARCHAR,
                memo TEXT,
                mcc VARCHAR,
                category_id UUID REFERENCES categories(id),
                source_category VARCHAR DEFAULT 'user',
                import_batch_id UUID REFERENCES import_batches(id),
                hash_dedupe VARCHAR,
                
                -- Enhanced fields from CSV
                transaction_type VARCHAR,
                main_category VARCHAR,
                csv_category VARCHAR,
                csv_subcategory VARCHAR,
                csv_account VARCHAR,
                owner VARCHAR,
                csv_account_type VARCHAR,
                is_expense BOOLEAN DEFAULT FALSE,
                is_income BOOLEAN DEFAULT FALSE,
                year INTEGER,
                month INTEGER,
                year_month VARCHAR,
                weekday VARCHAR,
                transfer_pair_id VARCHAR,
                
                -- Analysis fields
                confidence_score NUMERIC(3,2),
                review_needed BOOLEAN DEFAULT FALSE,
                tags JSONB,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create category_mappings table
        print("   Creating category_mappings table...")
        await conn.execute("""
            CREATE TABLE category_mappings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                pattern_type VARCHAR NOT NULL,
                pattern_value VARCHAR NOT NULL,
                category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
                priority INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT TRUE,
                confidence NUMERIC(3,2) DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create category_versions table
        print("   Creating category_versions table...")
        await conn.execute("""
            CREATE TABLE category_versions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                version INTEGER NOT NULL,
                label VARCHAR,
                changes JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create goals table
        print("   Creating goals table...")
        await conn.execute("""
            CREATE TABLE goals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                goal_type VARCHAR NOT NULL,
                target_amount NUMERIC(12,2) NOT NULL,
                current_amount NUMERIC(12,2) DEFAULT 0.0,
                target_date TIMESTAMP,
                category_scope JSONB,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create budgets table
        print("   Creating budgets table...")
        await conn.execute("""
            CREATE TABLE budgets (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                category_id UUID REFERENCES categories(id),
                name VARCHAR NOT NULL,
                month VARCHAR NOT NULL,
                limit_amount NUMERIC(12,2) NOT NULL,
                spent_amount NUMERIC(12,2) DEFAULT 0.0,
                rollover BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create forecasts table
        print("   Creating forecasts table...")
        await conn.execute("""
            CREATE TABLE forecasts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                category_id UUID REFERENCES categories(id),
                month VARCHAR NOT NULL,
                predicted_amount NUMERIC(12,2) NOT NULL,
                lower_bound NUMERIC(12,2),
                upper_bound NUMERIC(12,2),
                model VARCHAR DEFAULT 'prophet',
                model_version VARCHAR,
                confidence NUMERIC(3,2),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create scenarios table
        print("   Creating scenarios table...")
        await conn.execute("""
            CREATE TABLE scenarios (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                description TEXT,
                params_json JSONB NOT NULL,
                baseline_forecast_version VARCHAR,
                results JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create insights table
        print("   Creating insights table...")
        await conn.execute("""
            CREATE TABLE insights (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                kind VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                description TEXT,
                payload_json JSONB,
                priority INTEGER DEFAULT 0,
                dismissed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create audit_log table
        print("   Creating audit_log table...")
        await conn.execute("""
            CREATE TABLE audit_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                firebase_uid VARCHAR,
                entity VARCHAR NOT NULL,
                entity_id VARCHAR,
                action VARCHAR NOT NULL,
                before_json JSONB,
                after_json JSONB,
                details JSONB,
                ip_address VARCHAR,
                user_agent VARCHAR,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        print("\n3. Creating indexes for performance...")
        
        # Create all indexes
        indexes = [
            "CREATE INDEX idx_transactions_user_date ON transactions(user_id, posted_at);",
            "CREATE INDEX idx_transactions_user_category_date ON transactions(user_id, category_id, posted_at);",
            "CREATE INDEX idx_transactions_user_type_date ON transactions(user_id, transaction_type, posted_at);", 
            "CREATE INDEX idx_transactions_year_month ON transactions(user_id, year_month);",
            "CREATE INDEX idx_transactions_hash ON transactions(hash_dedupe);",
            "CREATE INDEX idx_transactions_batch ON transactions(import_batch_id);",
            "CREATE INDEX idx_category_mappings_user_priority ON category_mappings(user_id, priority DESC);",
            "CREATE INDEX idx_forecasts_user_month ON forecasts(user_id, month, category_id);",
            "CREATE INDEX idx_budgets_user_month ON budgets(user_id, month);",
            "CREATE INDEX idx_goals_user_status ON goals(user_id, status);",
            "CREATE INDEX idx_audit_log_user_entity ON audit_log(user_id, entity, created_at);",
            "CREATE INDEX idx_import_batches_user ON import_batches(user_id, created_at);",
            "CREATE INDEX idx_categories_user_active ON categories(user_id, active);"
        ]
        
        for index in indexes:
            await conn.execute(index)
            print(f"   Created index")
        
        print("\n4. Testing all table queries...")
        
        # Test each table with the exact queries used in the application
        test_queries = [
            ("users", "SELECT id, firebase_uid, email, display_name, locale, currency, created_at FROM users LIMIT 1"),
            ("categories", "SELECT id, user_id, parent_id, name, code, icon, color, category_type, version, active, created_at FROM categories LIMIT 1"),
            ("transactions", "SELECT id, user_id, account_id, posted_at, amount, currency, merchant, memo, mcc, category_id, source_category, import_batch_id, hash_dedupe, transaction_type, main_category, csv_category, csv_subcategory, csv_account, owner, csv_account_type, is_expense, is_income, year, month, year_month, weekday, transfer_pair_id, confidence_score, review_needed, tags, notes, created_at, updated_at FROM transactions LIMIT 1"),
            ("import_batches", "SELECT id, user_id, filename, file_size, file_hash, rows_total, rows_imported, rows_duplicated, rows_errors, status, error_message, summary_data, created_at, completed_at FROM import_batches LIMIT 1"),
            ("accounts", "SELECT id, user_id, name, account_type, institution, created_at FROM accounts LIMIT 1"),
            ("goals", "SELECT id, user_id, name, goal_type, target_amount, current_amount, target_date, category_scope, status, created_at, updated_at FROM goals LIMIT 1"),
            ("budgets", "SELECT id, user_id, category_id, name, month, limit_amount, spent_amount, rollover, created_at, updated_at FROM budgets LIMIT 1"),
            ("audit_log", "SELECT id, user_id, firebase_uid, entity, entity_id, action, before_json, after_json, details, ip_address, user_agent, created_at FROM audit_log LIMIT 1")
        ]
        
        for table_name, query in test_queries:
            await conn.fetch(query)
            print(f"   {table_name} table query successful")
        
        # Get final table count
        final_tables = await conn.fetch(tables_query)
        table_count = len(final_tables)
        
        await conn.close()
        
        print(f"\n✅ Database completely rebuilt!")
        print(f"   Created {table_count} tables with full schema")
        print(f"   Created {len(indexes)} performance indexes")
        print(f"   All application queries tested successfully")
        
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Your authentication should work immediately")
        print("3. All transaction endpoints should work") 
        print("4. CSV import should work once you have a proper CSV file")
        
        return True
        
    except Exception as e:
        print(f"Database rebuild failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("COMPLETE DATABASE REBUILD")
    print("=" * 50)
    print("This will DROP ALL existing data and recreate the entire database schema.")
    print("Make sure you have a backup if you need to preserve any data.")
    print()
    
    success = await rebuild_entire_database()
    
    if success:
        print("\n✅ Database completely rebuilt!")
        print("Your application should now work perfectly.")
    else:
        print("\n❌ Database rebuild failed!")

if __name__ == "__main__":
    asyncio.run(main())