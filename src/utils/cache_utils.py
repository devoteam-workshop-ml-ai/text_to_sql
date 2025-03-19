import sqlite3
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


####################################
# Gestion du cache (SQLite)        #
####################################


def get_cache_conn():
    """Retourne une connexion à la base cache (cache.db) en créant la table si nécessaire."""
    conn = sqlite3.connect("cache.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            sql_query TEXT,
            response TEXT
        )
    """
    )
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
    cursor.execute(
        "INSERT INTO cache (user_query, sql_query, response) VALUES (?, ?, ?)",
        (user_query, sql_query, response),
    )
    conn.commit()
    conn.close()


def get_cached_response(query: str, threshold: float = 0.8, field: str = "user_query"):
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
    texts = [row[0] if field == "user_query" else row[1] for row in rows]
    vectorizer = TfidfVectorizer().fit(texts + [query])
    vec_texts = vectorizer.transform(texts)
    vec_query = vectorizer.transform([query])
    similarities = cosine_similarity(vec_query, vec_texts).flatten()
    best_index = similarities.argmax()
    if similarities[best_index] >= threshold:
        return rows[best_index]
    return None
