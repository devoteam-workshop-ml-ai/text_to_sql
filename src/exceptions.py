class CachedResponseFoundError(Exception):
    """
    Exception levée lorsqu'une requête SQL similaire est trouvée dans le cache.
    Contient la réponse mise en cache.
    """

    def __init__(self, response):
        self.response = response
