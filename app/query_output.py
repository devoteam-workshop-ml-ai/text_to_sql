from typing_extensions import Annotated
from typing_extensions import TypedDict

from db import db
from llm import llm
from state import State
from query_prompt import query_prompt_template

from _utils.dump_utils import dump_data

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]

def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    try:
        dump_data(result["query"])
    except Exception as e:
        print(f"Error dumping query to file : {e}", )
    return {"query": result["query"]}