from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool

from state import State
from db import db

def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}