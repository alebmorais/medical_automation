#!/usr/bin/env python3
"""
Populate snippets.db from snippets_data.sql.

Usage (PowerShell):
  C:/Users/YourUser/AppData/Local/Programs/Python/Python311/python.exe load_snippets.py
  # or specify custom paths
  C:/.../python.exe load_snippets.py --db "path/to/snippets.db" --sql "path/to/snippets_data.sql"

This script will:
- Ensure the 'snippets' table exists
- Execute all statements in the provided SQL file (includes DELETE + INSERTs)
"""
import os
import sys
import sqlite3
import argparse

DEFAULT_DB = "snippets.db"
DEFAULT_SQL = "snippets_data.sql"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abbreviation TEXT NOT NULL UNIQUE,
    phrase TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def main():
    parser = argparse.ArgumentParser(description="Populate snippets.db from SQL file")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to snippets.db (default: snippets.db)")
    parser.add_argument("--sql", default=DEFAULT_SQL, help="Path to snippets_data.sql (default: snippets_data.sql)")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    sql_path = os.path.abspath(args.sql)

    if not os.path.exists(sql_path):
        print(f"ERROR: SQL file not found: {sql_path}")
        sys.exit(1)

    # Ensure directory exists for DB
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    try:
        with sqlite3.connect(db_path) as conn:
            # Ensure schema exists first
            conn.executescript(SCHEMA_SQL)
            # Apply data script
            with open(sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            conn.executescript(sql_script)
        print(f"✓ Loaded data from {sql_path} into {db_path}")
    except Exception as e:
        print(f"ERROR applying SQL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
