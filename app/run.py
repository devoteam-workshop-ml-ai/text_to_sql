import streamlit as st
from graph import graph, config
from credentials import _set_env
import sqlite3  # Remplacez par votre base de données
import os
# Vérifier si on a déjà une requête stockée
if "sql_query" not in st.session_state:
    st.session_state.sql_query = None
if "sql_result" not in st.session_state:
    st.session_state.sql_result = None

# Configuration des clés API
#_set_env("LANGCHAIN_API_KEY")

if not os.environ.get("GROQ_API_KEY"):
    groq_token = st.text_input("Entrez votre clé API Groq :")
    _set_env(groq_token)
else:
    _set_env("GROQ_API_KEY")

# Interface utilisateur
st.title("Générateur de Requêtes SQL")
question = st.text_input("Entrez votre question en langage naturel :")

if st.button("Générer la requête SQL") and question:
    response = ""
    for step in graph.stream({"question": question}, config, stream_mode="updates"):
        response += str(step) + "\n"
    
    # Stocker la requête générée
    st.session_state.sql_query = response

# Affichage de la requête générée si disponible
if st.session_state.sql_query:
    st.text_area("Requête SQL générée :", st.session_state.sql_query, height=150)

    # Bouton pour exécuter la requête
    if st.button("Appuyer pour exécuter la requête générée"):
        try:
            final_rep = ""
            for step in graph.stream(None, config, stream_mode="updates"):
                final_rep += str(step) + "\n"
            
            # Stocker le résultat pour l'afficher même après rerun
            st.session_state.sql_result = final_rep
        except Exception as e:
            st.error(f"Erreur lors de l'exécution : {e}")

# Affichage du résultat si disponible
if st.session_state.sql_result:
    st.text_area("Résultats de la requête :", st.session_state.sql_result, height=150)