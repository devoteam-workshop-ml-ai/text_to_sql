import sqlite3
import streamlit as st
import re
from pathlib import Path
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_groq import ChatGroq
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with SQL DB")

INJECTION_WARNING = """
                    SQL agent can be vulnerable to prompt injection. Use a DB role with limited permissions.
                    Read more [here](https://python.langchain.com/docs/security).
                    """
LOCALDB = "USE_LOCALDB"

# Choix de la source de la base de données
radio_opt = ["Use sample database - Chinook.db", "Connect to your SQL database"]
selected_opt = st.sidebar.radio(label="Choose suitable option", options=radio_opt)
if radio_opt.index(selected_opt) == 1:
    st.sidebar.warning(INJECTION_WARNING, icon="⚠️")
    db_uri = st.sidebar.text_input(
        label="Database URI", placeholder="mysql://user:pass@hostname:port/db"
    )
else:
    db_uri = LOCALDB

groq_api_key = st.sidebar.text_input(
    label="GROQ_API_KEY",
    type="password",
)

if not db_uri:
    st.info("Please enter database URI to connect to your database.")
    st.stop()

if not groq_api_key:
    st.info("Please add your GROQ API key to continue.")
    st.stop()

# Configuration du rate limiter (6000 tokens / bucket pour GROQ)
rate_limiter = InMemoryRateLimiter(
    max_bucket_size=6000,
)

# Setup LLM agent
llm = ChatGroq(
    groq_api_key=groq_api_key,
    model="llama3-8b-8192",
    streaming=True,
    temperature=0,
    rate_limiter=rate_limiter,
    max_tokens=6000
)

@st.cache_resource(ttl="2h")
def configure_db(db_uri):
    if db_uri == LOCALDB:
        # Connexion en lecture seule pour réduire les risques d'injection
        db_filepath = (Path(__file__).parent.parent / "data" / "database" / "Chinook.db").absolute()
        print("db_filepath : ", db_filepath)
        creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    return SQLDatabase.from_uri(database_uri=db_uri)

db = configure_db(db_uri)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

####################################
# Gestion du cache (SQLite)        #
####################################

def get_cache_conn():
    """Retourne une connexion à la base cache (cache.db) en créant la table si nécessaire."""
    conn = sqlite3.connect("cache.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            sql_query TEXT,
            response TEXT
        )
    """)
    conn.commit()
    return conn

def extract_sql_query(response_text: str) -> str:
    """
    Extrait la requête SQL de la réponse en cherchant une ligne débutant par 'sql_db_query:'.
    """
    match = re.search(r"sql_db_query:\s*(.*)", response_text)
    if match:
        return match.group(1).strip()
    return ""

def add_to_cache(user_query: str, sql_query: str, response: str):
    """Ajoute une entrée dans le cache."""
    conn = get_cache_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cache (user_query, sql_query, response) VALUES (?, ?, ?)",
                   (user_query, sql_query, response))
    conn.commit()
    conn.close()

def get_cached_response(query: str, threshold: float = 0.8, field: str = 'user_query'):
    """
    Cherche dans le cache une entrée dont le texte (du champ user_query ou sql_query)
    est similaire à la requête `query` (selon un seuil de similarité).
    Retourne un tuple (user_query, sql_query, response) si trouvé, sinon None.
    """
    conn = get_cache_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT user_query, sql_query, response FROM cache")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return None
    texts = [row[0] if field == 'user_query' else row[1] for row in rows]
    vectorizer = TfidfVectorizer().fit(texts + [query])
    vec_texts = vectorizer.transform(texts)
    vec_query = vectorizer.transform([query])
    similarities = cosine_similarity(vec_query, vec_texts).flatten()
    best_index = similarities.argmax()
    if similarities[best_index] >= threshold:
        return rows[best_index]
    return None

############################################
# Callback personnalisé pour la réflexion #
############################################

class CachedResponseFound(Exception):
    """
    Exception levée lorsqu'une requête SQL similaire est trouvée dans le cache.
    Contient la réponse mise en cache.
    """
    def __init__(self, response):
        self.response = response

class CustomSQLCallbackHandler(BaseCallbackHandler):
    """
    Callback qui intercepte les actions de l'agent. Lorsqu'une action contenant une requête SQL
    est détectée, il vérifie si une requête SQL similaire est présente dans le cache.
    Si oui, il lève une exception pour interrompre la réflexion et renvoyer la réponse en cache.
    """
    def on_agent_action(self, action, **kwargs):
        # Supposons que l'action possède un attribut 'tool_input' contenant le texte de la requête SQL.
        sql_query = getattr(action, "tool_input", "")
        if sql_query:
            cached = get_cached_response(sql_query, threshold=0.8, field='sql_query')
            if cached is not None:
                raise CachedResponseFound(cached[2])
        # Ne rien retourner, ou éventuellement faire d'autres traitements

####################################
# Gestion de l'historique de chat  #
####################################

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

####################################
# Traitement de la requête utilisateur
####################################

user_query = st.chat_input(placeholder="Ask me anything!")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)
    
    # 1. Vérifier dans le cache si une requête utilisateur similaire existe
    cached_entry = get_cached_response(user_query, threshold=0.7, field='user_query')
    if cached_entry is not None:
        cached_response = cached_entry[2]
        st.session_state.messages.append({"role": "assistant", "content": cached_response})
        st.chat_message("assistant").write(cached_response)
    else:
        try:
            with st.chat_message("assistant"):
                # On passe une liste de callbacks :
                # - notre callback personnalisé qui intercepte la réflexion
                # - le callback Streamlit pour l'affichage
                callbacks = [
                    CustomSQLCallbackHandler(),
                    StreamlitCallbackHandler(st.container())
                ]
                response = agent.run(input=user_query, callbacks=callbacks, handle_parsing_errors=True)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)
                # Extraction de la requête SQL générée dans la réponse finale
                sql_query = extract_sql_query(response)
                add_to_cache(user_query, sql_query, response)
        except CachedResponseFound as e:
            # Si une requête SQL similaire est trouvée durant la réflexion, renvoyer la réponse en cache.
            response = e.response
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
        except ValueError as e:
            st.error("⚠️ Une erreur est survenue lors du traitement de votre requête. Essayez de reformuler votre question.")
            st.session_state.messages.append({"role": "assistant", "content": "Je n'ai pas pu comprendre votre question. Pouvez-vous la reformuler ?"})
        except Exception as e:
            st.error(f"🚨 Erreur inattendue : {str(e)}")
