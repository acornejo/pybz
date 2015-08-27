import requests

class API(object):
    def __init__(self, base_url, ssl_verify = True):
        self.base_url = base_url
        self.ssl_verify = ssl_verify
        self.headers = {"User-Agent": 'pybz-rest'}
        self.token = None

        if self.base_url is None or self.base_url == "":
            self.handle_error('base_url not optional')

        if not self.base_url.endswith("/"):
            self.base_url = self.base_url + "/"

        if not self.base_url.endswith("rest/"):
            self.base_url = self.base_url + "rest/"

        if not self.ssl_verify:
            requests.packages.urllib3.disable_warnings()

        self.session = requests.Session()

    def handle_error(self, message):
        raise Exception (message)

    def request(self, method, path, **kwargs):
        url = self.base_url + path
        kwargs['headers'] = self.headers
        kwargs['verify'] = self.ssl_verify
        try:
            return self.session.request(method, url, **kwargs).json()
        except:
            return {'message': "Invalid rest endpoint '%s'"%url}

    def login(self, username, password):
        if username is None or password is None or password == "":
            self.handle_error('Cannot login without username and password')
        else:
            result = self.request('GET', 'login', params = {
                'login': username,
                'password': password})
            if 'token' in result:
                self.token = result['token']
                self.session.params['token'] = self.token
            else:
                self.handle_error(result['message'])

    def logout(self):
        if self.token:
            result = self.request('GET', 'logout')
            if 'message' in result:
                self.handle_error(result['message'])

    def bug_get(self, params):
        result = self.request('GET', 'bug', params = params)
        if 'bugs' in result:
            return result['bugs']
        else:
            self.handle_error(result['message'])

    def bug_set(self, params):
        bid = params['ids'][0]
        print params
        result = self.request('PUT', 'bug/' + str(bid), data = params)
        if 'bugs' in result:
            return result['bugs']
        else:
            self.handle_error(result['message'])

    def bug_new(self, params):
        result = self.request('POST', 'bug', data = params)
        if 'bugs' in result:
            return result['bugs']
        else:
            self.handle_error(result['message'])

    def list_fields(self):
        result = self.request('GET', 'field/bug')
        if 'fields' in result:
            return [f['name'] for f in result['fields'] if 'name' in f
                    and f['name'] != 'bug_id']
        else:
            self.handle_error("can't retrieve fields: '%s'" % result['message'])

    def list_products(self):
        result = self.request('GET', 'product', {'type': 'accessible'})
        if 'products' in result:
            return [p['name'] for p in result['products'] if 'name' in p]
        else:
            self.handle_error("can't retrieve products: '%s'" % result['message'])

    def list_components(self, product):
        result = self.request('GET', 'product', {'names': product})
        if 'products' in result:
            for p in result['products']:
                if 'name' in p and p['name'].lower() == product.lower():
                    return [c['name'] for c in p['components']]
        else:
            self.handle_error("can't retrieve components: '%s'" % result['message'])
