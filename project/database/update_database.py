import sqlite3
import os

def update_database(db_path='cdss.db'):
    """Safely update database schema"""

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("   Run init_db.py first to create the database")
        return False

    print("=" * 70)
    print("🔧 CDSS Database Schema Update")
    print("=" * 70)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current schema
        cursor.execute("PRAGMA table_info(consultations)")
        columns = {row[1] for row in cursor.fetchall()}

        print(f"✓ Found consultations table with {len(columns)} columns")

        updates_made = 0

        # Add vitals_data column if it does not exists
        if 'vitals_data' not in columns:
            print("  Adding vitals_data column...")
            cursor.execute("ALTER TABLE consultations ADD COLUMN vitals_data TEXT")
            updates_made += 1
            print("  ✓ Added vitals_data")
        else:
            print("  ✓ vitals_data already exists")

        # Add risk_scores_data column if it does not exist
        if 'risk_scores_data' not in columns:
            print("  Adding risk_scores_data column...")
            cursor.execute("ALTER TABLE consultations ADD COLUMN risk_scores_data TEXT")
            updates_made += 1
            print("  ✓ Added risk_scores_data")
        else:
            print("  ✓ risk_scores_data already exists")

        # Add duration_ms if not exist [might be called processing_time_ms]
        if 'duration_ms' not in columns and 'processing_time_ms' not in columns:
            print("  Adding duration_ms column...")
            cursor.execute("ALTER TABLE consultations ADD COLUMN duration_ms INTEGER")
            updates_made += 1
            print("  ✓ Added duration_ms")
        else:
            print("  ✓ duration_ms already exists")

        # Commit changes
        conn.commit()

        # Verify
        cursor.execute("PRAGMA table_info(consultations)")
        new_columns = {row[1] for row in cursor.fetchall()}

        print()
        print("=" * 70)
        print(f"✅ UPDATE COMPLETE")
        print("=" * 70)
        print(f"✓ Columns before: {len(columns)}")
        print(f"✓ Columns after: {len(new_columns)}")
        print(f"✓ Changes made: {updates_made}")
        print()

        if updates_made > 0:
            print("New columns added:")
            for col in new_columns - columns:
                print(f"  • {col}")
        else:
            print("Database already up to date!")

        print("=" * 70)

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else 'cdss.db'

    success = update_database(db_path)

    if success:
        print()
        print("🎉 You're ready to use CDSS v2.0!")
        print()
        print("Next steps:")
        print("  1. Start the server: python app.py")
        print("  2. Visit: http://localhost:5000")
        print("  3. Test with meningitis/appendicitis cases")
    else:
        print()
        print("⚠️  Update failed - check error messages above")
        sys.exit(1)
