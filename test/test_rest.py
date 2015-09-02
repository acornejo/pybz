from unittest import TestCase
from pybz import rest
import config
import uuid


class TestListingCommands(TestCase):
    def setUp(self):
        self.api = rest.API(config.endpoint['url'])
        self.bad_product = uuid.uuid4()

    def test_list_products(self):
        products = self.api.list_products()
        assert len(products) > 0

    def test_list_fields(self):
        fields = self.api.list_fields()
        assert 'product' in fields
        assert 'priority' in fields
        assert len(fields) > 0

    def test_list_compoents(self):
        products = self.api.list_products()
        found_components = False
        for product in products:
            components = self.api.list_components(product)
            if len(components) > 0:
                found_components = True
                break
        assert found_components

        with self.assertRaises(Exception):
            self.api.list_components(self.bad_product)
