import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_database(db_path='cdss.db', schema_path='schema.sql'):
    """
    Initialize CDSS database with full schema and seed data
    """

    print("=" * 70)
    print("🏥 CDSS v2.0 - DATABASE INITIALIZATION")
    print("=" * 70)
    print()

    # Check if the schema file exists
    if not os.path.exists(schema_path):
        print(f"❌ Error: Schema file not found: {schema_path}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Please ensure {schema_path} exists in the current directory.")
        sys.exit(1)

    # Backup existing database so we don't lose everything
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"📦 Existing database backed up to: {backup_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not backup database: {e}")

    # Connect to the database
    print(f"📂 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Read and execute schema
    print(f"📄 Loading schema from: {schema_path}")
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()

        # Execute schema split by semicolon for multiple statements
        cursor.executescript(schema)
        print("✅ Schema loaded successfully")
    except Exception as e:
        print(f"❌ Error loading schema: {e}")
        conn.close()
        sys.exit(1)

    # Create demo accounts
    print()
    print("👥 Creating demo user accounts...")

    try:
        # Admin account
        admin_hash = generate_password_hash("admin123")
        cursor.execute("""
            INSERT OR REPLACE INTO users
            (id, username, password_hash, email, full_name, role, institution,
             specialty, is_active, must_accept_disclaimer, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1, 'admin', admin_hash, 'admin@cdss.local',
            'System Administrator', 'admin', 'CDSS System',
            'Administration', 1, 0, 1
        ))
        print("   ✅ Admin account: admin / admin123")

        # Doctor account
        doctor_hash = generate_password_hash("doctor123")
        cursor.execute("""
            INSERT OR IGNORE INTO users
            (username, password_hash, email, full_name, role, institution,
             specialty, license_number, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'doctor', doctor_hash, 'doctor@cdss.local',
            'Dr. Jane Smith', 'doctor', 'General Hospital',
            'Internal Medicine', 'MD12345', 1
        ))
        print("   ✅ Doctor account: doctor / doctor123")

        # Student account
        student_hash = generate_password_hash("student123")
        cursor.execute("""
            INSERT OR IGNORE INTO users
            (username, password_hash, email, full_name, role, institution, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'student', student_hash, 'student@medschool.edu',
            'John Doe', 'student', 'Medical School', 1
        ))
        print("   ✅ Student account: student / student123")

        # Researcher account
        researcher_hash = generate_password_hash("research123")
        cursor.execute("""
            INSERT OR IGNORE INTO users
            (username, password_hash, email, full_name, role, institution,
             specialty, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'researcher', researcher_hash, 'research@cdss.local',
            'Dr. Research Smith', 'researcher', 'Research Institute',
            'Clinical Research', 1
        ))
        print("   ✅ Researcher account: researcher / research123")

    except Exception as e:
        print(f"   ❌ Error creating demo accounts: {e}")
        conn.rollback()
        conn.close()
        sys.exit(1)

    # Add initial system metrics
    print()
    print("📊 Initializing system metrics...")
    try:
        metrics = [
            ('system_initialized', 1.0, 'boolean', 'system'),
            ('database_version', 2.0, 'version', 'system'),
            ('model_accuracy_top1', 95.4, 'percent', 'performance'),
            ('model_accuracy_top3', 99.6, 'percent', 'performance'),
            ('diseases_count', 41, 'count', 'model'),
            ('symptoms_count', 133, 'count', 'model')
        ]

        for metric_name, value, unit, category in metrics:
            cursor.execute("""
                INSERT INTO system_metrics (metric_name, metric_value, metric_unit, metric_category)
                VALUES (?, ?, ?, ?)
            """, (metric_name, value, unit, category))

        print(f"   ✅ Added {len(metrics)} initial metrics")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not add metrics: {e}")

    # Commit all changes
    conn.commit()

    # Verification
    print()
    print("🔍 Verifying database...")

    try:
        # Check users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        print(f"   ✅ Users table: {user_count} users")

        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row['name'] for row in cursor.fetchall()]
        print(f"   ✅ Tables created: {len(tables)}")
        for table in tables:
            print(f"      • {table}")

        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) as count FROM sqlite_master
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        index_count = cursor.fetchone()['count']
        print(f"   ✅ Indexes created: {index_count}")

        # Check views
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view'
        """)
        views = [row['name'] for row in cursor.fetchall()]
        if views:
            print(f"   ✅ Views created: {len(views)}")
            for view in views:
                print(f"      • {view}")

        # Check triggers
        cursor.execute("""
            SELECT COUNT(*) as count FROM sqlite_master
            WHERE type='trigger'
        """)
        trigger_count = cursor.fetchone()['count']
        print(f"   ✅ Triggers created: {trigger_count}")

    except Exception as e:
        print(f"   ⚠️  Verification error: {e}")

    # Close the connection
    conn.close()

    # Success messages in terminal
    print()
    print("=" * 70)
    print("✅ DATABASE INITIALIZATION COMPLETE")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT SECURITY NOTICE:")
    print("   The demo accounts use default passwords.")
    print("   CHANGE THESE PASSWORDS BEFORE PRODUCTION DEPLOYMENT!")
    print()
    print("📋 Next steps:")
    print("   1. Ensure trained_model.json is in the project root")
    print("   2. Run: python app.py")
    print("   3. Open: http://localhost:5000")
    print()
    print("🎉 You're ready to start diagnosing!")
    print("=" * 70)


def verify_database(db_path='cdss.db'):
    """
    Verify database integrity
    """
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Run integrity checks
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()

        conn.close()

        if result[0] == 'ok':
            print("✅ Database integrity check passed")
            return True
        else:
            print(f"❌ Database integrity check failed: {result[0]}")
            return False

    except Exception as e:
        print(f"❌ Database verification error: {e}")
        return False


def reset_database(db_path='cdss.db'):
    """
    Reset database (delete and reinitialize)
    """
    print("⚠️  WARNING: This will DELETE all data!")
    confirm = input("Type 'yes' to confirm: ")

    if confirm.lower() != 'yes':
        print("❌ Reset cancelled")
        return

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Deleted: {db_path}")

    init_database(db_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='CDSS Database Management')
    parser.add_argument('--reset', action='store_true', help='Reset database')
    parser.add_argument('--verify', action='store_true', help='Verify database')
    parser.add_argument('--db', default='cdss.db', help='Database path')
    parser.add_argument('--schema', default='schema.sql', help='Schema file path')

    args = parser.parse_args()

    if args.reset:
        reset_database(args.db)
    elif args.verify:
        verify_database(args.db)
    else:
        init_database(args.db, args.schema)
