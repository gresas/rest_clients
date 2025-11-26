from .eve_rest import EveApiRest
from .exceptions import MissingConfigurationException


class EveClient(EveApiRest):

    def __init__(self, url, auth_handler = None):
        if not url:
            raise MissingConfigurationException(
                f'Missing required parameter url: {url}, auth_handler: {auth_handler}'
            )

        self.auth_handler = auth_handler
        self.url = url
