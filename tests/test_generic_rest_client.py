import pytest
from unittest.mock import patch, MagicMock
from rest_clients._generic_rest import RestClient
from rest_clients.exceptions import MissingConfigurationException


def test_init_ok():
    client = RestClient("http://example.com")
    assert client.url == "http://example.com"


def test_init_missing_url():
    with pytest.raises(MissingConfigurationException):
        RestClient("")


@patch("rest_clients._generic_rest.Session")
@patch("rest_clients._generic_rest.HTTPAdapter")
def test_retry_session_creates_session(mock_adapter, mock_session):

    session_instance = MagicMock()
    mock_session.return_value = session_instance

    client = RestClient("http://example.com")
    session = client._retry_session(retries=5, backoff_factor=0.7)

    assert session == session_instance
    mock_adapter.assert_called_once()
    session_instance.mount.assert_any_call("http://", mock_adapter.return_value)
    session_instance.mount.assert_any_call("https://", mock_adapter.return_value)


@pytest.fixture
def rest_client():
    return RestClient("http://example.com")


@patch.object(RestClient, "_retry_session")
def test_get_calls_retry_session(mock_session, rest_client):
    mock_client = MagicMock()
    mock_session.return_value = mock_client

    rest_client._get("http://example.com/test", timeout=3)
    mock_client.get.assert_called_once_with("http://example.com/test", timeout=3)


@patch.object(RestClient, "_retry_session")
def test_post_calls_retry_session(mock_session, rest_client):
    mock_client = MagicMock()
    mock_session.return_value = mock_client

    rest_client._post("http://example.com/post", json={"a": 1})
    mock_client.post.assert_called_once_with("http://example.com/post", json={"a": 1})


@patch.object(RestClient, "_retry_session")
def test_put_calls_retry_session(mock_session, rest_client):
    mock_client = MagicMock()
    mock_session.return_value = mock_client

    rest_client._put("http://example.com/put", data={"a": 1})
    mock_client.put.assert_called_once_with("http://example.com/put", data={"a": 1})


@patch.object(RestClient, "_retry_session")
def test_patch_calls_retry_session(mock_session, rest_client):
    mock_client = MagicMock()
    mock_session.return_value = mock_client

    rest_client._patch("http://example.com/patch", data={"a": 1})
    mock_client.patch.assert_called_once_with("http://example.com/patch", data={"a": 1})


@patch.object(RestClient, "_retry_session")
def test_delete_calls_retry_session(mock_session, rest_client):
    mock_client = MagicMock()
    mock_session.return_value = mock_client

    rest_client._delete("http://example.com/delete", timeout=1)
    mock_client.delete.assert_called_once_with("http://example.com/delete", timeout=1)


def test_require_auth_missing(rest_client):
    with pytest.raises(MissingConfigurationException):
        rest_client._require_auth()


def test_require_auth_ok(rest_client):
    rest_client.auth_handler = MagicMock()
    rest_client._require_auth()
