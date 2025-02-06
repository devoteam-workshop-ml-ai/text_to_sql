from langgraph.graph import START, StateGraph

from state import State

from query_output import write_query
from query_executor import execute_query
from answer import generate_answer

graph_builder = StateGraph(State).add_sequence(
    [write_query, execute_query, generate_answer]
)
graph_builder.add_edge(START, "write_query")
# graph = graph_builder.compile()
