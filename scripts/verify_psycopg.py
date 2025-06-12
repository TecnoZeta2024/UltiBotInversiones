import sys

try:
    import psycopg
    print("SUCCESS: psycopg was imported successfully.")
    sys.exit(0)
except ImportError as e:
    print(f"ERROR: Failed to import psycopg. Details: {e}", file=sys.stderr)
    sys.exit(1)
