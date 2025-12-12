from search_engine import interpret, fetch

def semantic_tool(query: str):
    """
    Interprets the user's query to find business category, city, and confidence score.
    """
    return interpret(query)

def sql_tool(category: str, city: str, limit=5):
    """
    Fetches the top business listings from the database.
    Returns a list of dictionaries and the generated SQL query.
    """
    df, sql = fetch(category, city, limit)
    return {
        "data": df.to_dict("records"),
        "sql": sql
    }