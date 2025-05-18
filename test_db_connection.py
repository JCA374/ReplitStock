# test_db_connection.py
from data.db_connection import get_db_connection, test_connection
import pandas as pd
from sqlalchemy import text


def run_comprehensive_test():
    """Run a comprehensive test of the database connection"""
    print("\n=== DATABASE CONNECTION TEST ===\n")

    # Test basic connection
    print("Testing basic connection...")
    connection_ok = test_connection()

    if not connection_ok:
        print("❌ Basic connection test failed. Cannot continue.")
        return False

    # Get database connection
    db = get_db_connection()
    engine = db.get_engine()
    connection_type = db.connection_type

    print(f"\nUsing {connection_type.upper()} database")

    # Test creating a temporary table
    print("\nTesting table creation...")
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS connection_test (
                    id SERIAL PRIMARY KEY,
                    test_name VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ Created test table successfully")

            # Insert test data
            conn.execute(text("""
                INSERT INTO connection_test (test_name) 
                VALUES ('IPv4 connection test')
            """))
            conn.commit()
            print("✅ Inserted test data successfully")

            # Query the data
            result = conn.execute(
                text("SELECT * FROM connection_test")).fetchall()
            print(f"✅ Retrieved {len(result)} row(s) from test table")
            for row in result:
                print(f"  - ID: {row[0]}, Name: {row[1]}, Timestamp: {row[2]}")

            # Clean up (optional)
            if connection_type == "postgresql":
                # Only delete rows in PostgreSQL to preserve evidence
                conn.execute(text("DELETE FROM connection_test"))
                conn.commit()
                print("✅ Cleaned up test data")
            else:
                # In SQLite, drop the table entirely
                conn.execute(text("DROP TABLE connection_test"))
                conn.commit()
                print("✅ Dropped test table")

    except Exception as e:
        print(f"❌ Error during database operations: {e}")
        return False

    print("\n✅ All database tests passed successfully!")
    return True


if __name__ == "__main__":
    run_comprehensive_test()
