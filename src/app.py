import streamlit as st

from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler

from langchain.agents.agent_toolkits import SQLDatabaseToolkit

from callbacks import CustomSQLCallbackHandler
from db import (
    INJECTION_WARNING,
    LOCALDB,
    configure_db
)
from exceptions import CachedResponseFoundError
from llm import llm
from utils.cache_utils import (
    add_to_cache,
    get_cached_response,
    extract_sql_query
)


if __name__ == "__main__":
    st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
    st.title("🦜 LangChain: Chat with SQL DB")

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

    db = configure_db(db_uri)

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

    # Assign GROQ API KEY
    llm.groq_api_key = groq_api_key

    # Setup LLM Agent
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    )

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
            except CachedResponseFoundError as e:
                # Si une requête SQL similaire est trouvée durant la réflexion, renvoyer la réponse en cache.
                response = e.response
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
            except ValueError as e:
                st.error("⚠️ Une erreur est survenue lors du traitement de votre requête. Essayez de reformuler votre question.")
                st.session_state.messages.append({"role": "assistant", "content": "Je n'ai pas pu comprendre votre question. Pouvez-vous la reformuler ?"})
            except Exception as e:
                st.error(f"🚨 Erreur inattendue : {str(e)}")
