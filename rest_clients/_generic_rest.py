import logging
from requests import Session
from requests.adapters import HTTPAdapter
from typing import Optional
from urllib3 import Retry
from .exceptions import MissingConfigurationException


logger = logging.getLogger(__name__)


class RestClient:
    DEFAULT_TIMEOUT = 5
    BASE_HEADERS = {
        "Cache-Control": "no-cache",
    }

    def __init__(self, url: str):
        if not url:
            raise MissingConfigurationException("Missing required parameter 'url'")
        self.url = url

    @staticmethod
    def _retry_session(
        retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: tuple = (404, 500, 501, 502, 503, 504, 505),
        session: Optional[Session] = None,
    ) -> Session:
        session = session or Session()

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _delete(self, *a, **kw):
        return self._retry_session().delete(*a, **kw)

    def _get(self, *a, **kw):
        return self._retry_session().get(*a, **kw)

    def _patch(self, *a, **kw):
        return self._retry_session().patch(*a, **kw)

    def _post(self, *a, **kw):
        return self._retry_session().post(*a, **kw)

    def _put(self, *a, **kw):
        return self._retry_session().put(*a, **kw)

    def _require_auth(self):
        if not hasattr(self, "auth_handler") or not self.auth_handler:
            raise MissingConfigurationException("Auth property must be set")
