import os
import sys
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error

def load_environment() -> Dict[str, Any]:
    """
    Load environment variables from .env file if it exists
    """
    load_dotenv()
    
    env_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL')
    }
    
    return env_vars

def check_requirements() -> Dict[str, bool]:
    """
    Check if all required dependencies are installed
    """
    requirements = {
        'langchain': True,
        'openai': True,
        'pgvector': True,
        'psycopg2': True,
        'sentence_transformers': True
    }
    
    try:
        import langchain
    except ImportError:
        requirements['langchain'] = False
        
    try:
        import openai
    except ImportError:
        requirements['openai'] = False
        
    try:
        import pgvector
    except ImportError:
        requirements['pgvector'] = False
        
    try:
        import psycopg2
    except ImportError:
        requirements['psycopg2'] = False
        
    try:
        import sentence_transformers
    except ImportError:
        requirements['sentence_transformers'] = False
        
    return requirements

def setup_environment() -> bool:
    """
    Set up the environment for the application.
    Returns True if setup was successful, False otherwise.
    """
    # Load environment variables
    env_vars = load_environment()
    
    # Check for required API keys
    if not env_vars.get('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your environment or in a .env file.")
        return False
        
    # Check for database connection string
    if not env_vars.get('DATABASE_URL'):
        print("WARNING: DATABASE_URL environment variable is not set.")
        print("Using default connection string from config.py")
        
    # Check for required packages
    requirements = check_requirements()
    missing_packages = [pkg for pkg, installed in requirements.items() if not installed]
    
    if missing_packages:
        print(f"ERROR: The following required packages are missing: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
        
    return True

def parse_connection_string(connection_string: str) -> Tuple[str, str, str, str, str]:
    """
    Parse a SQLAlchemy connection string into individual components.
    
    Args:
        connection_string: SQLAlchemy connection string format
                          Example: postgresql+psycopg2://postgres:password@localhost:5433/smartbeauty
    
    Returns:
        Tuple of (host, port, user, password, dbname)
    """
    try:
        # Extract the part after postgresql+psycopg2://
        params_part = connection_string.split("://")[1]
        
        # Split user:password@host:port/dbname
        user_pass, host_port_db = params_part.split("@")
        user, password = user_pass.split(":")
        
        # Handle host:port/dbname
        if "/" in host_port_db:
            host_port, dbname = host_port_db.split("/")
        else:
            host_port, dbname = host_port_db, ""
            
        # Handle host:port
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host, port = host_port, "5432"
            
        return host, port, user, password, dbname
    except Exception as e:
        raise ValueError(f"Failed to parse connection string: {e}")

def create_db_connection(connection_string: str) -> Optional[psycopg2.extensions.connection]:
    """
    Create a PostgreSQL database connection using the connection string from config.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        psycopg2 connection object or None if connection fails
    """
    try:
        host, port, user, password, dbname = parse_connection_string(connection_string)
        
        print(f"Connecting to {host}:{port} as {user} to database {dbname}")
        
        # Create a direct connection using psycopg2
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
        
        print("Successfully connected to the PostgreSQL database!")
        return conn
        
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def test_db_connection(connection_string: str, table_name: str = None) -> bool:
    """
    Test database connection and optionally check if a table exists.
    
    Args:
        connection_string: Database connection string
        table_name: Optional table name to check for existence
        
    Returns:
        True if connection successful (and table exists if specified), False otherwise
    """
    conn = create_db_connection(connection_string)
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Check if table exists (if table_name is provided)
        if table_name:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            
            table_exists = cursor.fetchone()[0]
            if table_exists:
                print(f"The table '{table_name}' exists!")
                
                # Count rows
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"Table '{table_name}' has {count} rows.")
            else:
                print(f"The table '{table_name}' does not exist.")
                return False
                
        # Close cursor and connection
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"Error testing database: {e}")
        if conn:
            conn.close()
        return False
