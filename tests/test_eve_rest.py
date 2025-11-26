import pytest
from unittest.mock import MagicMock, patch
from rest_clients.eve_rest import EveApiRest
from rest_clients.exceptions import ApiRestException, MissingConfigurationException


@pytest.fixture
def client():
    c = EveApiRest("http://example.com")
    c.auth_handler = MagicMock()
    c.auth_handler.get_token.return_value = "TOKEN"
    return c


def test_init_missing_url():
    with pytest.raises(MissingConfigurationException):
        EveApiRest("")


def test_init_ok():
    c = EveApiRest("http://x.com")
    assert c.url == "http://x.com"


def test_auth_headers(client):
    assert client._auth_headers({"A": "1"}) == {
        "Authorization": "TOKEN",
        "A": "1",
    }


def test_auth_headers_no_extra(client):
    assert client._auth_headers() == {"Authorization": "TOKEN"}


@patch.object(EveApiRest, "_retry_session")
def test_status(mock_retry, client):
    sess = MagicMock()
    mock_retry.return_value = sess

    resp = MagicMock()
    resp.json.return_value = {"ok": True}
    sess.get.return_value = resp

    assert client.status() == {"ok": True}
    sess.get.assert_called_once_with("http://example.com/status")


@patch.object(EveApiRest, "_get")
def test_get(mock_get, client):
    resp = MagicMock()
    resp.json.return_value = {"value": 10}
    mock_get.return_value = resp

    result = client.get("123")
    assert result == {"value": 10}
    mock_get.assert_called_once()


@patch.object(EveApiRest, "_get")
def test_get_items_by_id(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "_items": [{"_id": "b"}, {"_id": "a"}]
    }
    mock_get.return_value = mock_resp

    ids = ["a", "b"]
    res = client.get_items_by_id(ids, ordered=True)
    assert res["_items"] == [{"_id": "a"}, {"_id": "b"}]


@patch.object(EveApiRest, "_retry_operation")
def test_post_success(mock_retry, client):
    resp = MagicMock()
    resp.json.return_value = {"_id": "xyz"}
    mock_retry.return_value = resp

    out = client.post({"a": 1})
    assert out == resp


@patch.object(EveApiRest, "_retry_operation")
@patch.object(EveApiRest, "get")
def test_post_return_resource(mock_get, mock_retry, client):
    resp = MagicMock()
    resp.json.return_value = {"_id": "abc"}
    mock_retry.return_value = resp

    mock_get.return_value = {"_id": "abc", "name": "Guilherme"}

    result = client.post({"x": 1}, return_resource=True)
    assert result == {"_id": "abc", "name": "Guilherme"}


@patch.object(EveApiRest, "_retry_operation", side_effect=Exception("boom"))
def test_post_exception(mock_retry, client):
    with pytest.raises(ApiRestException):
        client.post({"x": 1})


@patch.object(EveApiRest, "_retry_operation")
@patch.object(EveApiRest, "get")
def test_patch_success(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "ET"}
    resp = MagicMock()
    mock_retry.return_value = resp

    r = client.patch("id1", {"a": "b"})
    assert r == resp


@patch.object(EveApiRest, "_retry_operation", side_effect=Exception("err"))
@patch.object(EveApiRest, "get")
def test_patch_exception(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "ET"}
    with pytest.raises(ApiRestException):
        client.patch("id1", {"x": 1})


@patch.object(EveApiRest, "_retry_operation")
@patch.object(EveApiRest, "get")
def test_delete_success(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "TT"}
    resp = MagicMock()
    mock_retry.return_value = resp

    r = client.delete("id1")
    assert r == resp


@patch.object(EveApiRest, "_retry_operation", side_effect=Exception("fail"))
@patch.object(EveApiRest, "get")
def test_delete_exception(mock_get, mock_retry, client):
    mock_get.return_value = {"_etag": "EE"}
    with pytest.raises(ApiRestException):
        client.delete("id1")


def test_retry_operation_refresh_token(client):
    r403 = MagicMock()
    r403.ok = False
    r403.status_code = 403
    r403.reason = "Forbidden"

    rok = MagicMock()
    rok.ok = True

    sequence = [r403, rok]

    def fake_func(*a, **kw):
        return sequence.pop(0)

    with patch("rest_clients.eve_rest.sleep"):
        result = client._retry_operation(tries=2, func=fake_func)

    assert result.ok is True
    client.auth_handler.update_token.assert_called_once()


def test_retry_operation_fail_last_try(client):
    r_fail = MagicMock()
    r_fail.ok = False
    r_fail.status_code = 500
    r_fail.reason = "Error"
    r_fail.raise_for_status.side_effect = Exception("raised")

    def fn(*a, **kw):
        return r_fail

    with patch("rest_clients.eve_rest.sleep"):
        with pytest.raises(Exception):
            client._retry_operation(tries=2, func=fn)
