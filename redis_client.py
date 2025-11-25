from typing import Any, Dict, List, Optional, Tuple
from redis import StrictRedis
from redis.sentinel import Sentinel, MasterNotFoundError


class RedisClient:
    """
    A wrapper around Redis or Redis Sentinel that ensures connection to a master node
    and provides common Redis operations.
    """

    def __init__(self, config: Dict[str, Any]):
        if not isinstance(config, dict):
            raise ValueError(f"Invalid connection parameters: {config}")

        self.redis_properties = config
        self.connection_params = self._build_connection_params(config)
        self.redis_client = self._init_master_client()

    @staticmethod
    def _build_connection_params(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the connection parameters for either standalone Redis or Sentinel.
        """
        timeout = config.get("socket_timeout", 0.1)

        if "cluster" in config and config["cluster"]:
            cluster_nodes: List[Tuple[str, int]] = []
            for entry in config["cluster"]:
                host, port = entry.split(":")
                cluster_nodes.append((host, int(port)))

            return {
                "cluster": cluster_nodes,
                "socket_timeout": timeout,
            }

        return {
            "host": config.get("host", "localhost"),
            "port": config.get("port", 6379),
            "password": config.get("password"),
            "socket_timeout": timeout
        }

    def _connect(self):
        """
        Connect to Redis or Sentinel depending on configuration.
        """
        if "cluster" in self.connection_params:
            sentinel = Sentinel(
                self.connection_params["cluster"],
                socket_timeout=self.connection_params["socket_timeout"]
            )
            return sentinel.master_for("mymaster")

        return StrictRedis(
            host=self.connection_params["host"],
            port=self.connection_params["port"],
            password=self.connection_params.get("password"),
            socket_timeout=self.connection_params["socket_timeout"],
        )

    def _init_master_client(self):
        """
        Connect to Redis and ensure the node is a master.
        """
        client = self._connect()
        info = client.info()

        if info.get("role") != "master":
            raise MasterNotFoundError(f"Expected master but connected to: {info.get('role')}")

        return client

    def ping(self) -> bool:
        return self.redis_client.ping()

    def set_value(self, key: str, value: Any, ex: Optional[int] = None):
        """Set value of a key with optional expiration time."""
        self.redis_client.set(name=key, value=value, ex=ex)

    def get_value(self, key: str) -> Any:
        """Get the value of a key."""
        return self.redis_client.get(key)

    def delete_key(self, key: str):
        """Delete a key."""
        self.redis_client.delete(key)

    def key_exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(self.redis_client.exists(key))

    def expire_key(self, key: str, seconds: int):
        """Set a timeout on a key."""
        self.redis_client.expire(key, seconds)

    def hash_set_value(self, hash_key: str, field: str, value: Any):
        self.redis_client.hset(hash_key, field, value)

    def hash_get_value(self, hash_key: str, field: str) -> Any:
        return self.redis_client.hget(hash_key, field)

    def hash_get_all(self, hash_key: str) -> Dict[bytes, bytes]:
        return self.redis_client.hgetall(hash_key)

    def hash_set_multiple(self, hash_key: str, mapping: Dict[str, Any]):
        self.redis_client.hset(hash_key, mapping=mapping)

    def hash_delete_field(self, hash_key: str, *fields: str):
        self.redis_client.hdel(hash_key, *fields)
