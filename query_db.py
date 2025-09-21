#!/usr/bin/env python3
import psycopg2
import sys
import os
import re
import argparse
from urllib.parse import urlparse

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

def connect_to_db(config_num=1):
    """Connect to PostgreSQL database using environment variables for specified config."""
    print("Attempting to connect to database...")
    
    # Select configuration based on config_num
    if config_num == 1:
        db_url = os.getenv('DATABASE_URL')
        prefix = 'DB_'
    else:
        db_url = os.getenv(f'DATABASE_URL_{config_num}')
        prefix = f'DB_{config_num}_'
    
    if db_url:
        print(f"Using DATABASE_URL{'' if config_num == 1 else f'_{config_num}'} connection")
        parsed = urlparse(db_url)
        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            connect_timeout=10
        )
    else:
        host = os.getenv(f'{prefix}HOST', 'localhost')
        port = int(os.getenv(f'{prefix}PORT', 5432))
        database = os.getenv(f'{prefix}NAME', 'postgres')
        user = os.getenv(f'{prefix}USER', 'postgres')
        password = os.getenv(f'{prefix}PASSWORD', '')
        
        print(f"Using config {config_num}: {user}@{host}:{port}/{database}")
        return psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10
        )

def is_read_only_query(query):
    """Check if query is read-only by blocking dangerous keywords."""
    query_upper = query.upper()
    
    # Blocked keywords that modify data
    blocked_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
        'CALL', 'DO', 'COPY', 'MERGE', 'UPSERT'
    ]
    
    # Remove comments and normalize whitespace
    cleaned_query = re.sub(r'--.*$', '', query_upper, flags=re.MULTILINE)
    cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
    cleaned_query = ' '.join(cleaned_query.split())
    
    # Check for blocked keywords
    for keyword in blocked_keywords:
        if re.search(r'\b' + keyword + r'\b', cleaned_query):
            return False, f"Blocked keyword detected: {keyword}"
    
    # Must start with SELECT
    if not cleaned_query.startswith('SELECT'):
        return False, "Only SELECT queries are allowed"
    
    return True, "Query is read-only"

def format_table_horizontal(rows, columns):
    """Format results as a horizontal table."""
    if not rows:
        return "No results found"
    
    # Truncate long values and limit column widths
    max_col_width = 20
    truncated_rows = []
    
    for row in rows:
        truncated_row = []
        for val in row:
            str_val = str(val) if val is not None else ''
            if len(str_val) > max_col_width:
                truncated_row.append(str_val[:max_col_width-3] + '...')
            else:
                truncated_row.append(str_val)
        truncated_rows.append(truncated_row)
    
    # Truncate column names too
    truncated_columns = []
    for col in columns:
        if len(col) > max_col_width:
            truncated_columns.append(col[:max_col_width-3] + '...')
        else:
            truncated_columns.append(col)
    
    if HAS_TABULATE:
        return tabulate(truncated_rows, headers=truncated_columns, tablefmt='grid')
    else:
        # Simple table formatting with truncated data
        col_widths = [min(max_col_width, max(len(str(col)), max(len(str(row[i])) for row in truncated_rows))) for i, col in enumerate(truncated_columns)]
        
        # Header
        header = '| ' + ' | '.join(col.ljust(col_widths[i]) for i, col in enumerate(truncated_columns)) + ' |'
        separator = '+' + '+'.join('-' * (width + 2) for width in col_widths) + '+'
        
        result = [separator, header, separator]
        
        # Rows
        for row in truncated_rows:
            row_str = '| ' + ' | '.join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + ' |'
            result.append(row_str)
        
        result.append(separator)
        return '\n'.join(result)

def format_table_vertical(rows, columns):
    """Format results vertically for better readability."""
    if not rows:
        return "No results found"
    
    result = []
    
    for row_index, row in enumerate(rows):
        result.append(f"\n--- Record {row_index + 1} ---")
        
        # Find the maximum column name length for alignment
        max_col_len = max(len(col) for col in columns)
        
        for col_index, col_name in enumerate(columns):
            value = row[col_index] if row[col_index] is not None else ''
            result.append(f"{col_name.ljust(max_col_len)}: {value}")
    
    return '\n'.join(result)

def format_table(rows, columns, vertical=True, max_cols_horizontal=10):
    """Format results based on display preference and column count."""
    if not rows:
        return "No results found"
    
    # Auto-detect if we should use vertical format
    if not vertical and len(columns) > max_cols_horizontal:
        print(f"Too many columns ({len(columns)}), switching to vertical display")
        vertical = True
    
    if vertical:
        return format_table_vertical(rows, columns)
    else:
        return format_table_horizontal(rows, columns)

def run_query(query, vertical=True, verbose=False, config_num=1):
    """Run a SELECT query and return up to 10 rows."""
    query = query.strip()
    if verbose:
        print(f"Query to execute: {query}")
        print(f"Using database config: {config_num}")
    
    # Security check: ensure read-only query
    if verbose:
        print("Validating query safety...")
    is_safe, message = is_read_only_query(query)
    if not is_safe:
        raise ValueError(message)
    if verbose:
        print("Query validation passed")
    
    # Add LIMIT if not present
    if 'LIMIT' not in query.upper():
        query += ' LIMIT 10'
        if verbose:
            print("Added LIMIT 10 to query")
    
    try:
        conn = connect_to_db(config_num)
        if verbose:
            print("Database connection established")
        cursor = conn.cursor()
        
        if verbose:
            print("Executing query...")
        cursor.execute(query)
        
        if verbose:
            print("Fetching results...")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        if verbose:
            print(f"Retrieved {len(rows)} rows")
        # Print formatted table
        print(format_table(rows, columns, vertical))
            
        cursor.close()
        conn.close()
        if verbose:
            print("Database connection closed")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Execute read-only PostgreSQL queries safely',
        epilog='''
Examples:
  %(prog)s "SELECT * FROM users LIMIT 5"
  %(prog)s --horizontal "SELECT id, name FROM products"
  %(prog)s -f query.sql --verbose
  %(prog)s -v "SELECT COUNT(*) FROM orders"
  %(prog)s --config 2 "SELECT * FROM reservations"

Environment Variables:
  For config 1 (default):
    DATABASE_URL                    Full database connection string
    OR use individual variables:
    DB_HOST                        Database host (default: localhost)
    DB_PORT                        Database port (default: 5432)
    DB_NAME                        Database name (default: postgres)
    DB_USER                        Database user (default: postgres)
    DB_PASSWORD                    Database password (default: empty)

  For config 2:
    DATABASE_URL_2                 Full database connection string
    OR use individual variables:
    DB_2_HOST                      Database host
    DB_2_PORT                      Database port
    DB_2_NAME                      Database name
    DB_2_USER                      Database user
    DB_2_PASSWORD                  Database password

Security:
  - Only SELECT queries are allowed
  - Blocks INSERT, UPDATE, DELETE, DROP, etc.
  - Automatically adds LIMIT 10 if not specified
  - 10-second connection timeout
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Query input options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('query', nargs='?', help='SQL query string to execute')
    group.add_argument('-f', '--file', help='File containing SQL query to execute')
    
    # Database configuration
    parser.add_argument('--config', '-c', type=int, default=1, choices=[1, 2],
                       help='Database configuration to use (1 or 2, default: 1)')
    
    # Display options
    parser.add_argument('--horizontal', action='store_true', 
                       help='Display results in horizontal table format (default: vertical)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output for debugging')
    
    args = parser.parse_args()
    
    # Get query from file or command line
    if args.file:
        try:
            with open(args.file, 'r') as f:
                query = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    else:
        query = args.query
    
    # Display format (vertical by default)
    vertical = not args.horizontal
    
    if not query:
        parser.print_help()
        sys.exit(1)
    
    run_query(query, vertical=vertical, verbose=args.verbose, config_num=args.config)
