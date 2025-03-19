import streamlit as st
import sqlite3

from pathlib import Path

from langchain.sql_database import SQLDatabase
from sqlalchemy import create_engine

INJECTION_WARNING = """
                    SQL agent can be vulnerable to prompt injection. Use a DB role with limited permissions.
                    Read more [here](https://python.langchain.com/docs/security).
                    """
LOCALDB = "USE_LOCALDB"


@st.cache_resource(ttl="2h")
def configure_db(db_uri):
    if db_uri == LOCALDB:
        # Connexion en lecture seule pour réduire les risques d'injection
        db_filepath = (
            Path(__file__).parent.parent / "data" / "database" / "Chinook.db"
        ).absolute()
        print("db_filepath : ", db_filepath)
        creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    return SQLDatabase.from_uri(database_uri=db_uri)
