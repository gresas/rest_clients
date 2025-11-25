import pytest
from unittest.mock import MagicMock, patch
from rest_clients.eve_rest import EveApiRest
from rest_clients.exceptions import ApiRestException, MissingConfigurationException


@pytest.fixture
def client():
    c = EveApiRest("http://example.com")
    c.auth_handler = MagicMock()
    c.auth_handler.get_token.return_value = "JWT TOKEN"

    c.auth_api = MagicMock()
    return c


def test_init_ok():
    c = EveApiRest("http://example.com")
    assert c.url == "http://example.com"


def test_init_missing_url():
    with pytest.raises(MissingConfigurationException):
        EveApiRest("")



def test_auth_headers(client):
    headers = client._auth_headers({"X-Test": "1"})
    assert headers == {
        "Authorization": "JWT TOKEN",
        "X-Test": "1",
    }


def test_auth_headers_without_extra(client):
    headers = client._auth_headers()
    assert headers == {"Authorization": "JWT TOKEN"}


@patch.object(EveApiRest, "_retry_session")
def test_status(mock_retry, client):
    mock_sess = MagicMock()
    mock_retry.return_value = mock_sess

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok"}
    mock_sess.get.return_value = mock_resp

    result = client.status()
    assert result == {"status": "ok"}
    mock_sess.get.assert_called_once_with("http://example.com/status")


@patch.object(EveApiRest, "_get")
def test_get(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"value": 123}
    mock_get.return_value = mock_resp

    res = client.get("abc")
    assert res == {"value": 123}
    mock_get.assert_called_once()


@patch.object(EveApiRest, "_get")
def test_get_items_by_id(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "_items": [
            {"_id": "b"},
            {"_id": "a"},
        ]
    }
    mock_get.return_value = mock_resp

    ids = ["a", "b"]
    result = client.get_items_by_id(ids, ordered=True)

    assert result["_items"] == [
        {"_id": "a"},
        {"_id": "b"},
    ]


@patch.object(EveApiRest, "_retry_operation")
def test_post_success(mock_retry, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"_id": "xyz"}
    mock_retry.return_value = mock_resp

    response = client.post({"a": 1})
    assert response == mock_resp

    mock_retry.assert_called_once()


@patch.object(EveApiRest, "get")
@patch.object(EveApiRest, "_retry_operation")
def test_post_return_resource(mock_retry, mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"_id": "xyz"}
    mock_retry.return_value = mock_resp

    mock_get.return_value = {"_id": "xyz", "name": "abc"}

    result = client.post({"a": 1}, return_resource=True)
    assert result == {"_id": "xyz", "name": "abc"}


@patch.object(EveApiRest, "_retry_operation", side_effect=Exception("fail"))
def test_post_exception(mock_retry, client):
    with pytest.raises(ApiRestException):
        client.post({"a": 1})


@patch.object(EveApiRest, "_retry_operation")
@patch.object(EveApiRest, "get")
def test_patch_ok(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "12345"}

    mock_resp = MagicMock()
    mock_retry.return_value = mock_resp

    resp = client.patch("item123", {"name": "new"})
    assert resp == mock_resp


@patch.object(EveApiRest, "_retry_operation", side_effect=Exception("boom"))
@patch.object(EveApiRest, "get")
def test_patch_exception(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "123"}

    with pytest.raises(ApiRestException):
        client.patch("id123", {"x": 1})


@patch.object(EveApiRest, "_retry_operation")
@patch.object(EveApiRest, "get")
def test_delete_ok(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "ETAG1"}

    mock_resp = MagicMock()
    mock_retry.return_value = mock_resp

    resp = client.delete("id111")
    assert resp == mock_resp


@patch.object(EveApiRest, "_retry_operation", side_effect=Exception("explode"))
@patch.object(EveApiRest, "get")
def test_delete_exception(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "AAA"}

    with pytest.raises(ApiRestException):
        client.delete("id222")


def test_retry_operation_403_refresh_token(client):
    response_403 = MagicMock()
    response_403.ok = False
    response_403.status_code = 403
    response_403.reason = "Forbidden"

    response_ok = MagicMock()
    response_ok.ok = True

    call_sequence = [response_403, response_ok]

    def fake_func(*a, **kw):
        return call_sequence.pop(0)

    with patch("rest_clients.eve_rest.sleep"):
        resp = client._retry_operation(tries=2, func=fake_func)

    assert resp.ok is True
    client.auth_api.update_token.assert_called_once()
