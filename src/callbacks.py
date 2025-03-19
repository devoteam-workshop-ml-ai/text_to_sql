from langchain.callbacks.base import BaseCallbackHandler

from exceptions import CachedResponseFoundError

from utils.cache_utils import get_cached_response


############################################
# Callback personnalisé pour la réflexion #
############################################

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
                raise CachedResponseFoundError(cached[2])
        # Ne rien retourner, ou éventuellement faire d'autres traitements