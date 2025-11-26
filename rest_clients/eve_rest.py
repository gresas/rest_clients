import json
import logging
from time import sleep
from typing import Any, Dict, List, Optional
from .exceptions import ApiRestException
from rest_clients._generic_rest import RestClient


logger = logging.getLogger(__name__)


class EveApiRest(RestClient):
    DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

    def _auth_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        self._require_auth()
        extra = extra or {}
        return {"Authorization": self.auth_handler.get_token(), **extra}

    def _retry_operation(self, tries: int, func, *args, **kwargs):
        for attempt in range(1, tries + 1):
            resp = func(*args, **kwargs)

            if resp.ok:
                return resp

            if resp.status_code == 403:
                logger.debug("403 received, refreshing token...")
                self.auth_handler.update_token()
                continue

            logger.warning(
                "Request failed: %s %s (attempt %d)",
                resp,
                resp.reason,
                attempt,
            )

            if attempt == tries:
                resp.raise_for_status()

            sleep(attempt)

        raise ApiRestException("Unexpected retry logic failure")

    @property
    def status_url(self) -> str:
        return f"{self.url}/status"

    def status(self) -> Dict[str, Any]:
        resp = self._retry_session(retries=1).get(self.status_url)
        resp.raise_for_status()
        return resp.json()

    def get(self, resource_id: str) -> Dict[str, Any]:
        resp = self._get(f"{self.url}/{resource_id}", headers=self.BASE_HEADERS)
        resp.raise_for_status()
        return resp.json()

    def get_items_by_id(self, ids: List[str], ordered: bool = False) -> Dict[str, Any]:
        where = json.dumps({"_id": {"$in": ids}})
        resp = self._get(self.url, params={"where": where})
        resp.raise_for_status()

        result = resp.json()
        if ordered:
            result["_items"] = sorted(result["_items"], key=lambda x: ids.index(x["_id"]))

        return result

    def post(
        self,
        payload: Dict[str, Any],
        return_resource: bool = False,
        exception=ApiRestException,
    ):
        self._require_auth()

        try:
            resp = self._retry_operation(
                tries=2,
                func=self._post,
                url=self.url,
                json=payload,
                headers=self._auth_headers(),
                timeout=self.DEFAULT_TIMEOUT,
            )
        except Exception as e:
            raise exception(f"Failed to POST to {self.url}: {e}") from e

        if return_resource:
            resource_id = resp.json().get("_id")
            return self.get(resource_id)

        return resp

    def patch(
        self,
        resource_id: str,
        payload: Dict[str, Any],
        exception=ApiRestException,
    ):
        self._require_auth()
        url = f"{self.url}/{resource_id}"

        try:
            data = self.get(resource_id)
            headers = self._auth_headers({"If-match": data["_etag"]})

            resp = self._retry_operation(
                tries=3,
                func=self._patch,
                url=url,
                json=payload,
                headers=headers,
            )
        except Exception as e:
            raise exception(f"Failed to PATCH {url}: {e}") from e

        logger.info("Patched successfully: %s", url)
        return resp

    def delete(self, resource_id: str, exception=ApiRestException):
        self._require_auth()
        url = f"{self.url}/{resource_id}"

        try:
            data = self.get(resource_id)
            headers = self._auth_headers({"If-match": data["_etag"]})

            resp = self._retry_operation(
                tries=3,
                func=self._delete,
                url=url,
                headers=headers,
            )
        except Exception as e:
            raise exception(f"Failed to DELETE {url}: {e}") from e

        logger.info("Deleted successfully: %s", url)
        return resp
