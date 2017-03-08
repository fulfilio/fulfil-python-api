import jwt
from requests_oauthlib import OAuth2Session


class Session(OAuth2Session):

    def __init__(
        self, client_id, client_secret, redirect_uri, scope, *args, **kwargs
    ):
        self.client_secret = client_secret
        super(Session, self).__init__(
            client_id, *args, redirect_uri=redirect_uri, scope=scope, **kwargs
        )

    def get_authorization_url(self):
        authorization_url = 'https://auth.fulfil.io/oauth/authorize'
        return self.authorization_url(authorization_url)

    def get_base_url(self, code):
        "fetches base_url from code"
        try:
            payload = jwt.decode(code, verify=False)
        except jwt.exceptions.InvalidTokenError:
            raise Exception('Invalid code')
        if payload['organization_id'] == 'localhost':
            return 'http://localhost:8000/'
        else:
            return 'https://%s/' % (
                payload['organization']['url']
            )

    def get_token(self, code):
        base_url = self.get_base_url(code)
        token_url = base_url + 'oauth/token'
        return self.fetch_token(
            token_url, client_secret=self.client_secret, code=code
        )
