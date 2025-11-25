import pytest
from unittest.mock import MagicMock, patch
from redis.sentinel import MasterNotFoundError
from .redis_client import RedisClient


def mock_master(role="master"):
    """Creates a mock Redis client with a fake INFO role."""
    client = MagicMock()
    client.info.return_value = {"role": role}
    return client


def test_invalid_config_raises():
    with pytest.raises(ValueError):
        RedisClient("not-a-dict")


@patch("rest_clients.redis_client.StrictRedis")
def test_standalone_master_connection(mock_redis):
    instance = mock_master("master")
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost", "port": 6379})

    assert client.redis_client is instance
    mock_redis.assert_called_once()


@patch("rest_clients.redis_client.StrictRedis")
def test_standalone_non_master_raises(mock_redis):
    instance = mock_master("slave")
    mock_redis.return_value = instance

    with pytest.raises(MasterNotFoundError):
        RedisClient({"host": "localhost", "port": 6379})


@patch("rest_clients.redis_client.Sentinel")
def test_sentinel_master_connection(mock_sentinel):
    master = mock_master("master")

    sentinel_instance = MagicMock()
    sentinel_instance.master_for.return_value = master
    mock_sentinel.return_value = sentinel_instance

    config = {"cluster": ["host1:26379", "host2:26379"]}
    client = RedisClient(config)

    sentinel_instance.master_for.assert_called_once_with("mymaster")
    assert client.redis_client is master


@patch("rest_clients.redis_client.Sentinel")
def test_sentinel_non_master_raises(mock_sentinel):
    sentinel_instance = MagicMock()
    sentinel_instance.master_for.return_value = mock_master("slave")
    mock_sentinel.return_value = sentinel_instance

    with pytest.raises(MasterNotFoundError):
        RedisClient({"cluster": ["host1:26379"]})


@patch("rest_clients.redis_client.StrictRedis")
def test_ping(mock_redis):
    instance = mock_master()
    instance.ping.return_value = True
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    assert client.ping() is True


@patch("rest_clients.redis_client.StrictRedis")
def test_set_value(mock_redis):
    instance = mock_master()
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    client.set_value("foo", "bar", ex=10)

    instance.set.assert_called_once_with(name="foo", value="bar", ex=10)


@patch("rest_clients.redis_client.StrictRedis")
def test_get_value(mock_redis):
    instance = mock_master()
    instance.get.return_value = b"bar"
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    value = client.get_value("foo")

    assert value == b"bar"
    instance.get.assert_called_once_with("foo")


@patch("rest_clients.redis_client.StrictRedis")
def test_delete_key(mock_redis):
    instance = mock_master()
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    client.delete_key("foo")

    instance.delete.assert_called_once_with("foo")


@patch("rest_clients.redis_client.StrictRedis")
def test_key_exists(mock_redis):
    instance = mock_master()
    instance.exists.return_value = 1
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    assert client.key_exists("foo") is True


@patch("rest_clients.redis_client.StrictRedis")
def test_expire_key(mock_redis):
    instance = mock_master()
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    client.expire_key("foo", 100)

    instance.expire.assert_called_once_with("foo", 100)


@patch("rest_clients.redis_client.StrictRedis")
def test_hash_set_value(mock_redis):
    instance = mock_master()
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    client.hash_set_value("hash", "field", "value")

    instance.hset.assert_called_once_with("hash", "field", "value")


@patch("rest_clients.redis_client.StrictRedis")
def test_hash_get_value(mock_redis):
    instance = mock_master()
    instance.hget.return_value = b"value"
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    assert client.hash_get_value("hash", "field") == b"value"


@patch("rest_clients.redis_client.StrictRedis")
def test_hash_get_all(mock_redis):
    instance = mock_master()
    instance.hgetall.return_value = {"f": b"v"}
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    assert client.hash_get_all("hash") == {"f": b"v"}


@patch("rest_clients.redis_client.StrictRedis")
def test_hash_set_multiple(mock_redis):
    instance = mock_master()
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    client.hash_set_multiple("hash", {"a": 1, "b": 2})

    instance.hset.assert_called_once_with("hash", mapping={"a": 1, "b": 2})


@patch("rest_clients.redis_client.StrictRedis")
def test_hash_delete_field(mock_redis):
    instance = mock_master()
    mock_redis.return_value = instance

    client = RedisClient({"host": "localhost"})
    client.hash_delete_field("hash", "a", "b")

    instance.hdel.assert_called_once_with("hash", "a", "b")
