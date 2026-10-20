import re

class SQLValidationError(Exception):
    pass

def validate_sql(query: str) -> bool:
    """
    Validates that the SQL query is safe and read-only.
    """
    if not query or not query.strip():
        raise SQLValidationError("Query cannot be empty.")
    
    # Remove SQL comments for validation
    query_no_comments = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    query_no_comments = re.sub(r'/\*.*?\*/', '', query_no_comments, flags=re.DOTALL)
    
    query_upper = query_no_comments.upper().strip()
    
    # Check for multiple statements
    if ';' in query_no_comments:
        parts = [p.strip() for p in query_no_comments.split(';') if p.strip()]
        if len(parts) > 1:
            raise SQLValidationError("Multiple statements are not allowed.")
    
    # Reject dangerous keywords
    forbidden_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", 
        "CREATE", "GRANT", "REVOKE", "COPY", "EXECUTE", "DO", "CALL"
    ]
    
    # Tokenize simply
    tokens = re.split(r'\s+', query_upper)
    
    for token in tokens:
        if token in forbidden_keywords:
            raise SQLValidationError(f"Forbidden keyword found: {token}. Only read-only queries are allowed.")
    
    # Ensure it starts with SELECT or WITH
    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        raise SQLValidationError("Query must start with SELECT or WITH.")
        
    return True
