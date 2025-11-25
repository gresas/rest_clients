from unittest import TestCase
from unittest.mock import Mock

from .exceptions import MissingConfigurationException
from .eve_client import EveClient

FAKE_URL = 'http://fake.url'


class TestGenericApiInit(TestCase):

    def test_should_validate_required_params(self):
        self.assertRaises(MissingConfigurationException, EveClient, None, None)
        self.assertRaises(MissingConfigurationException, EveClient, None, Mock())

    def test_should_instantiate_with_auth_handler(self):
        self.assertIsInstance(EveClient(FAKE_URL, Mock()), EveClient)
