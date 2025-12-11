# tools.py
from search_engine import interpret, fetch

def semantic_tool(query: str):
    result = interpret(query)
    return result

def sql_tool(category: str, city: str, limit=5):
    df, sql = fetch(category, city, limit)
    return {
        "data": df.to_dict("records"),
        "sql": sql
    }
