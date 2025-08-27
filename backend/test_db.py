import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        # Get connection string from .env
        conn_string = os.getenv("DATABASE_URL")
        
        if not conn_string:
            print("❌ No DATABASE_URL found in .env file")
            return False
            
        print(f"🔗 Testing connection to: {conn_string[:50]}...")
        
        # Connect to database
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Connected successfully!")
        print(f"📊 Database version: {version[0][:60]}...")
        
        # Test creating a simple table (will be replaced by our models)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        cursor.execute("INSERT INTO connection_test (message) VALUES (%s);", ("Phase 1 test successful!",))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM connection_test;")
        count = cursor.fetchone()[0]
        print(f"✅ Test table created and populated (rows: {count})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing NeonDB Connection...")
    success = test_connection()
    if success:
        print("\n🎉 Database is ready for Phase 1!")
    else:
        print("\n🔧 Please check your DATABASE_URL in .env file")