[![codecov](https://codecov.io/gh/gresas/rest_clients/branch/main/graph/badge.svg)](https://codecov.io/gh/gresas/rest_clients)

# rest_clients

Biblioteca leve para clientes REST e Redis, focada em casos de uso com APIs Eve (RESTful) e Redis/Sentinel.

## Visão geral

- Wrapper Redis que garante conexão com um nó *master* e operações comuns: [`rest_clients.redis_client.RedisClient`](redis_client.py).
- Cliente HTTP genérico com retry e helpers para métodos HTTP: [`rest_clients._generic_rest.RestClient`](_generic_rest.py).
- Extensão específica para APIs Eve com lógica de autenticação, retry e operações CRUD: [`rest_clients.eve_rest.EveApiRest`](eve_rest.py).
- Construtor simples do cliente Eve que valida a configuração: [`rest_clients.eve_client.EveClient`](eve_client.py).
- Exceções personalizadas para controle de erro: [`rest_clients.exceptions.ApiRestException`](exceptions.py) e [`rest_clients.exceptions.MissingConfigurationException`](exceptions.py).

## Arquivos importantes

- Código principal:
  - [`rest_clients.redis_client.RedisClient`](redis_client.py)
  - [`rest_clients._generic_rest.RestClient`](_generic_rest.py)
  - [`rest_clients.eve_rest.EveApiRest`](eve_rest.py)
  - [`rest_clients.eve_client.EveClient`](eve_client.py)
  - [`rest_clients.exceptions`](exceptions.py)
- Metadata e package:
  - [__init__.py](__init__.py)
  - [__version__.py](__version__.py)
- Testes:
  - [test_redis_client.py](test_redis_client.py)
  - [test_generic_rest_client.py](test_generic_rest_client.py)
  - [test_eve_rest.py](test_eve_rest.py)
  - [test_eve_client.py](test_eve_client.py)
- Licença:
  - [LICENSE](LICENSE)

## Instalação

Instale dependências (ex.: requests, redis) e importe os módulos do pacote.

## Exemplos de uso

- Redis (standalone)
```python
from rest_clients.redis_client import RedisClient

cfg = {"host": "localhost", "port": 6379}
rc = RedisClient(cfg)
rc.set_value("k", "v", ex=60)
val = rc.get_value("k")
```

- Redis com Sentinel
```python
cfg = {"cluster": ["host1:26379", "host2:26379"]}
rc = RedisClient(cfg)
```

- REST genérico
```python
from rest_clients._generic_rest import RestClient

client = RestClient("https://api.example.com")
resp = client._get("https://api.example.com/resource")
```

- Cliente Eve com autenticação
```python
from rest_clients.eve_client import EveClient

# auth_handler deve expor get_token() e update_token()
eve = EveClient("https://eve.example.com", auth_handler=my_auth_handler)
resp = eve.get("resource_id")
```

## Exceções relevantes

- `MissingConfigurationException` é lançada quando parâmetros obrigatórios (ex.: URL ou auth) não são fornecidos.
- `ApiRestException` é usada para erros de operação nas chamadas REST.

## Testes

Execute os testes com pytest:
```sh
pytest -q
```

## Licença

Projeto licenciado sob a [MIT License](LICENSE).
