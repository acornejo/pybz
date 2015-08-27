import meta
import bzrest
import keyring
import getpass
import ConfigParser
import argparse
import sys
import os

"""
on creation, cc and flags are arrays

"""

SPECIAL_FIELDS = {
'blocks': {'prefix': ['+', '-','='], 'field': ['add', 'remove','set'], 'type': int},
'dependson': {'prefix': ['+', '-','='], 'field': ['add', 'remove','set'],  'type': int},
'keyword': {'prefix': ['+', '-','='], 'field': ['add', 'remove','set'], 'type': str},
'alias': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
'see_also': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
'groups': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
'cc': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
'comment': {'field': 'body'}
}

CONFIG_FILE = os.path.expanduser('~/.pybz')
MANDATORY_FIELDS=["product", "component", "summary", "version"]
DEFAULT_OUTPUT_FIELDS=["id", "status", "priority", "summary"]

def print_error(msg):
    sys.stderr.write("pybz error: " + str(msg) + "\n")

def process_fields(fields, valid_fields, extra_processing={}):
    params = {}
    if fields:
        valid_fields = [f.lower() for f in valid_fields]
        for field in fields:
            name = field.split(":")[0].lower()
            value = (":".join(field.split(":")[1:])).strip()
            if name in valid_fields:
                if name not in extra_processing:
                    params[name] = value
                else:
                    if 'prefix' in extra_processing[name]:
                        try:
                            prefix = extra_processing[name]['prefix']
                            idx = map(value.startswith,prefix).index(True)
                            value = value[len(prefix[idx]):]
                            value = extra_processing[name]['type'](value)
                            field = extra_processing[name]['field'][idx]
                            if name not in params:
                                params[name] = {}
                            if field not in params[name]:
                                params[name][field] = []
                            params[name][field].append(value)
                        except:
                            raise Exception ("Field '%s' must start with one of '%s'"%(name, ",".join(prefix)))
                    else:
                        params[name] = {}
                        params[name][extra_processing['field']] = value
            else:
                raise Exception ("Invalid field name '%s'"%name)
    return params

def print_bug(b, output_fields):
    fields = []
    for f in output_fields:
        if f in b:
            fields.append(str(b[f]))
    print " ".join(fields)

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description=meta.DESCRIPTION + " " + meta.VERSION)
    parser.add_argument('--url', action='store', type=str,
            default=None, help='bugzilla server http url')
    parser.add_argument('--username', action='store', type=str,
            default=None, help='bugzilla username')
    parser.add_argument('--password', action='store', type=str,
            default=None, help='bugzilla password')
    parser.add_argument('-k', action='store_true', dest='ssl_verify',
            default=False, help='allow insecure SSL certificate')
    parser.add_argument('-K', action='store_true', dest='use_keyring',
            default=None, help='use keyring to store/retrieve password')

    subparser = parser.add_subparsers(dest='command', metavar='COMMAND')

    get_parser = subparser.add_parser('get', help='get bug information')
    get_parser.add_argument('bugnum', type=int, nargs='+', help='bug number')
    get_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
            nargs='+', action='store', default=None,
            help='fields used for search')
    get_parser.add_argument('-s', '--show-fields', metavar='FIELD', type=str,
            nargs='+', action='store', default=None, dest='show_fields',
            help='fields to return (default: id status priority summary)')

    set_parser = subparser.add_parser('set', help='set bug information')
    set_parser.add_argument('bugnum', type=int, nargs='+', help='bug number')
    set_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
            nargs='+', required=True, action='store', default=None,
            help='fields to be set')

    new_parser = subparser.add_parser('new', help='create new bug')
    new_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
            nargs='+', required=True, action='store', default=None,
            help='fields to be set')

    field_parser  = subparser.add_parser('list-fields',
            help='list all available bug fields')
    product_parser  = subparser.add_parser('list-products',
            help='list all available bug products')
    component_parser = subparser.add_parser('list-components',
            help='list all components for a given product')
    component_parser.add_argument('product', default=None, type=str,
            help='product name')

    args = parser.parse_args()

    # Config parser
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)

    # Read conncetion preferences from config and args
    base_url = None
    ssl_verify = True
    username = None
    password = None
    use_keyring = False
    api_params = {'base_url': None, 'ssl_verify': True}
    if config.has_option('core', 'url'):
        base_url = config.get('core', 'url')
    if config.has_option('core', 'ssl_verify'):
        ssl_verify = config.getboolean('core', 'ssl_verify')
    if config.has_option('core', 'username'):
        username = config.get('core', 'username')
    if config.has_option('core', 'use_keyring'):
        use_keyring = config.getboolean('core', 'use_keyring')
    if args.url is not None:
        base_url = args.url
    if args.ssl_verify is not None:
        ssl_verify = args.ssl_verify
    if args.username is not None:
        username = args.username
    if args.password is not None:
        password = args.password
    if args.use_keyring is not None:
        use_keyring  = args.use_keyring

    # Get password through keyring or stdin
    if username is not None:
        if password is None:
            if use_keyring:
                password = keyring.get_password('pybz', username)
            if password is None:
                if sys.stdin.isatty():
                    print "Username: ", username
                    password = getpass.getpass()
        if password is None or password == "":
            print_error('Cannot login without password')
            return 1
        elif use_keyring:
            keyring.set_password('pybz', username, password)

    try:
        # Create API connection
        api = bzrest.API(base_url, ssl_verify)

        # Login if appropriate
        if username and password:
            api.login(username, password)

        # Process commands
        if args.command == 'list-fields':
            for f in api.list_fields():
                print f
        elif args.command == 'list-products':
            for p in api.list_products():
                print p
        elif args.command == 'list-components':
            for c in api.list_components(args.product):
                print c
        elif args.command == 'get':
            output_fields = DEFAULT_OUTPUT_FIELDS
            if args.show_fields is not None:
                output_fields = args.show_fields
            params = {}
            if args.bugnum:
                params['id'] = args.bugnum
            params.update(process_fields(args.fields, api.list_fields()))
            for b in api.bug_get(params):
                print_bug (b, output_fields)
        elif args.command == 'set':
            params = {'ids': args.bugnum}
            params.update(process_fields(args.fields, api.list_fields(), SPECIAL_FIELDS))
            for b in api.bug_set(params):
                print b['id']
        elif args.command == 'new':
            params = process_fields(args.fields, api.list_fields())
            for f in MANDATORY_FIELDS:
                if f not in params:
                    print_error("Missing mandatory field '%s'"%f)
            b = api.bug_new(params)
            print b['id']

        if username and password:
            api.logout()
    except Exception as inst:
        print_error(inst)
        if username and password:
            api.logout()
        return 1

    return 0
