from unittest import TestCase
from pybz import rest
import uuid
import httpretty
import fixtures
import json
import re


class TestRest(TestCase):
    def setUp(self):
        self.url = 'https://mockserver.bugzilla.org/rest'
        httpretty.enable()

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    def test_user_auth(self):
        token = str(uuid.uuid4())
        username = str(uuid.uuid4())
        password = str(uuid.uuid4())
        httpretty.register_uri(httpretty.GET,
                               self.url + '/login',
                               content_type='application/json',
                               body=json.dumps({'token': token}))

        api = rest.API(self.url)
        api.login(username, password)
        assert 'login' in httpretty.last_request().querystring
        assert httpretty.last_request().querystring['login'][0] == username
        assert 'password' in httpretty.last_request().querystring
        assert httpretty.last_request().querystring['password'][0] == password

        httpretty.register_uri(httpretty.GET,
                               self.url + '/anymethod',
                               content_type='application/json',
                               body=json.dumps({'hello': 'world'}))

        api.request('GET', 'anymethod')
        assert 'token' in httpretty.last_request().querystring
        assert httpretty.last_request().querystring['token'][0] == token

        httpretty.register_uri(httpretty.GET,
                               self.url + '/logout',
                               content_type='application/json',
                               body=json.dumps({'hello': 'world'}))

        api.logout()
        api.request('GET', 'anymethod')
        assert 'token' not in httpretty.last_request().querystring

    def test_token_auth(self):
        token = str(uuid.uuid4())
        api = rest.API(self.url, token=token)

        httpretty.register_uri(httpretty.GET,
                               self.url + '/anymethod',
                               content_type='application/json',
                               body=json.dumps({'hello': 'world'}))

        api.request('GET', 'anymethod')
        assert 'token' in httpretty.last_request().querystring
        assert httpretty.last_request().querystring['token'][0] == token

        httpretty.register_uri(httpretty.GET,
                               self.url + '/logout',
                               content_type='application/json',
                               body=json.dumps({'hello': 'world'}))

        api.logout()
        api.request('GET', 'anymethod')
        assert 'token' not in httpretty.last_request().querystring

    def test_api_key_auth(self):
        api_key = str(uuid.uuid4())
        api = rest.API(self.url, api_key=api_key)

        httpretty.register_uri(httpretty.GET,
                               self.url + '/anymethod',
                               content_type='application/json',
                               body=json.dumps({'hello': 'world'}))

        api.request('GET', 'anymethod')
        assert 'api_key' in httpretty.last_request().querystring
        assert httpretty.last_request().querystring['api_key'][0] == api_key

        httpretty.register_uri(httpretty.GET,
                               self.url + '/logout',
                               content_type='application/json',
                               body=json.dumps({'hello': 'world'}))

        api.logout()
        api.request('GET', 'anymethod')
        assert 'api_key' in httpretty.last_request().querystring

    def test_list_products(self):
        httpretty.register_uri(httpretty.GET,
                               self.url + '/product',
                               content_type='application/json',
                               body=json.dumps(fixtures.products))

        api = rest.API(self.url)
        products = api.list_products()
        assert len(products) > 0
        assert 'type' in httpretty.last_request().querystring
        assert httpretty.last_request().querystring['type'][0] == 'accessible'

    def test_list_components(self):
        httpretty.register_uri(httpretty.GET,
                               self.url + '/product',
                               content_type='application/json',
                               body=json.dumps(fixtures.products))

        api = rest.API(self.url)
        components = api.list_components(fixtures.product_name)
        assert len(components) > 0
        assert 'names' in httpretty.last_request().querystring
        assert httpretty.last_request().querystring['names'][0] == \
            fixtures.product_name

    def test_list_fields(self):
        httpretty.register_uri(httpretty.GET,
                               self.url + '/field/bug',
                               content_type='application/json',
                               body=json.dumps(fixtures.fields))

        api = rest.API(self.url)
        fields = api.list_fields()
        assert len(fields) > 0
        assert httpretty.has_request()

    def test_bug_get(self):
        httpretty.register_uri(httpretty.GET,
                               self.url + '/bug',
                               content_type='application/json',
                               body=json.dumps(fixtures.bug1))
        api = rest.API(self.url)
        params = {}
        for i in range(10):
            params[str(uuid.uuid4())] = str(uuid.uuid4())
        bugs = api.bug_get(params)
        assert len(bugs) == 1
        for k, v in params.iteritems():
            assert k in httpretty.last_request().querystring
            assert httpretty.last_request().querystring[k][0] == v

    def test_bug_new(self):
        httpretty.register_uri(httpretty.POST,
                               self.url + '/bug',
                               content_type='application/json',
                               body=json.dumps(fixtures.bug1))

        api = rest.API(self.url)
        params = {}
        for i in range(10):
            params[str(uuid.uuid4())] = str(uuid.uuid4())
        bugs = api.bug_new(params)
        assert len(bugs) == 1
        for k, v in params.iteritems():
            assert k in httpretty.last_request().parsed_body
            assert httpretty.last_request().parsed_body[k] == v

    def test_bug_set(self):
        httpretty.register_uri(httpretty.PUT,
                               re.compile(self.url + '/bug/(\d+)'),
                               content_type='application/json',
                               body=json.dumps(fixtures.bug1))

        api = rest.API(self.url)
        ids = [12345]
        params = {}
        for i in range(10):
            params[str(uuid.uuid4())] = str(uuid.uuid4())
        params['ids'] = ids
        bugs = api.bug_set(params)
        assert len(bugs) == 1
        expected_url = '/rest/bug/' + str(ids[0])
        assert httpretty.last_request().path == expected_url
        for k, v in params.iteritems():
            assert k in httpretty.last_request().parsed_body
            assert httpretty.last_request().parsed_body[k] == v

    def test_bug_set_multiple(self):
        httpretty.register_uri(httpretty.PUT,
                               re.compile(self.url + '/bug/(\d+)'),
                               content_type='application/json',
                               body=json.dumps(fixtures.bug1))

        api = rest.API(self.url)
        ids = [12345, 13245, 143443]
        params = {}
        for i in range(10):
            params[str(uuid.uuid4())] = str(uuid.uuid4())
        params['ids'] = ids
        bugs = api.bug_set(params)
        assert len(bugs) == 1
        expected_url = '/rest/bug/' + str(ids[0])
        assert httpretty.last_request().path == expected_url
        for k, v in params.iteritems():
            assert k in httpretty.last_request().parsed_body
            assert httpretty.last_request().parsed_body[k] == v
