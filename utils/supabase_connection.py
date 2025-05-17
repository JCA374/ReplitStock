import os

def format_supabase_url():
    """
    Format the Supabase URL into a proper PostgreSQL connection string.
    
    If the DATABASE_URL is already in PostgreSQL format, return it unchanged.
    If it's in Supabase URL format, convert it to PostgreSQL format.
    
    Returns:
        str: Formatted PostgreSQL connection string
    """
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return None
    
    # If it's already in PostgreSQL format, return it as is
    if database_url.startswith("postgresql://"):
        return database_url
    
    # If it's a Supabase URL, convert it to PostgreSQL format
    if database_url.startswith("https://") and "supabase.co" in database_url:
        # Extract project reference from the URL
        project_ref = database_url.split("//")[1].split(".")[0]
        
        # We need the password from the user
        password = os.getenv("SUPABASE_DB_PASSWORD", "")
        
        if not password:
            print("ERROR: SUPABASE_DB_PASSWORD not set in environment variables")
            print("Please set the SUPABASE_DB_PASSWORD with your Supabase database password")
            return None
        
        # Format PostgreSQL connection string
        # Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
        postgres_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
        
        # Log success but hide actual password
        masked_url = postgres_url.replace(password, "********")
        print(f"Converted Supabase URL to PostgreSQL format: {masked_url}")
        
        return postgres_url
    
    # If it's neither, return as is (though it might not work)
    print("WARNING: Unrecognized DATABASE_URL format")
    return database_url

def get_postgres_connection_string():
    """Get a properly formatted PostgreSQL connection string."""
    return format_supabase_url()