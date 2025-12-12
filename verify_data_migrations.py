#!/usr/bin/env python
"""
Data migration script for legacy encryption format.
This is a one-time migration that was needed for old data.
Most installations don't need this anymore.
"""

import sys

try:
    from sqlalchemy import create_engine, text
    from config import Config

    # Use raw SQLAlchemy to avoid Flask-SQLAlchemy context issues
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

    with engine.connect() as conn:
        # Check if Meta table has any rows (indicates already migrated)
        result = conn.execute(text("SELECT COUNT(*) FROM meta")).fetchone()
        if result and result[0] > 0:
            # Already migrated
            sys.exit(0)

        # Check if notes table exists and has data
        result = conn.execute(text("SELECT COUNT(*) FROM note")).fetchone()
        if not result or result[0] == 0:
            # No notes to migrate
            sys.exit(0)

    # If we get here, we might need migration - but this is rare
    # The actual migration is complex and requires the full app context
    # For now, just print a warning
    print("Note: If you have very old data that needs encryption migration,")
    print("please run the migration manually with the full application context.")

except Exception as e:
    # Non-critical script - don't fail the startup
    print(f"Data migration check skipped: {e}")
    sys.exit(0)
