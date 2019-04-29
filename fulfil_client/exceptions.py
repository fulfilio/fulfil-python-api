class Error(Exception):
    def __init__(self, message, code):
        super(Exception, self).__init__(message)
        self.message = message
        self.code = code

    def __str__(self):
        return str(self.message)


class ServerError(Error):
    """
    Raised when the server returns an internal server error.
    It is unlikely to have any additional information on the
    body as this error was unexpected.
    """

    def __init__(self, message, code, sentry_id=None):
        super(ServerError, self).__init__(message, code)
        self.sentry_id = sentry_id


class ClientError(Error):
    pass


class AuthenticationError(ClientError):
    """
    Failure to properly authenticate yourself in the request.

    This could be because a token expired or becuase the auth
    is just invalid.
    """
    pass


class UserError(ClientError):
    """
    UserError is raised by the Fulfil Server when there
    is a data error or a validation fails. The error messages
    are meant to be user facing and should ideally be displayed
    to the user.
    """
    pass
