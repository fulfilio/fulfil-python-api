from requests_oauthlib import OAuth2Session


class Session(OAuth2Session):

    client_id = None
    client_secret = None

    def __init__(self, subdomain, **kwargs):
        client_id = self.client_id
        client_secret = self.client_secret
        self.fulfil_subdomain = subdomain
        if not (client_id and client_secret):
            raise Exception('Missing client_id or client_secret.')
        super(Session, self).__init__(client_id=client_id, **kwargs)

    @classmethod
    def setup(cls, client_id, client_secret):
        """Configure client in session
        """
        cls.client_id = client_id
        cls.client_secret = client_secret

    @property
    def base_url(self):
        if self.fulfil_subdomain == 'localhost':
            return 'http://localhost:8000/'
        else:
            return 'https://%s.fulfil.io/' % self.fulfil_subdomain

    def create_authorization_url(self, redirect_uri, scope, **kwargs):
        self.redirect_uri = redirect_uri
        self.scope = scope
        return self.authorization_url(
            self.base_url + 'oauth/authorize', **kwargs)

    def get_token(self, code):
        token_url = self.base_url + 'oauth/token'
        return self.fetch_token(
            token_url, client_secret=self.client_secret, code=code
        )
