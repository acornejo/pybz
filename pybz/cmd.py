import meta
import rest
import keyring
import getpass
import ConfigParser
import argparse
import sys
import os
import yaml

CONFIG_FILE = os.path.expanduser('~/.pybz')

MANDATORY_FIELDS = ["product", "component", "summary", "version"]

DEFAULT_FIELDS = ["id", "status", "priority", "summary"]

SETTABLE_FIELDS = [
    "alias", "assigned_to", "blocks", "depends_on", "cc",
    "comment", "component",   "deadline", "dupe_of", "estimated_time",
    "groups", "keywords", "op_sys", "platform", "priority", "product",
    "qa_contact", "reset_assigned_to", "reset_qa_contact", "resolution",
    "see_also", "status", "summary", "target_milestone", "url",
    "version", "whiteboard"]

CREATING_FIELDS = [
    "product", "component", "summary", "version", "description",
    "op_sys", "platform", "priority", "severity", "alias",
    "assigned_to", "cc", "groups", "qa_contact", "status", "resolution",
    "target_milestone"]

GETTING_FIELDS = [
    "alias", "assigned_to", "blocks", "cc", "classification",
    "component", "creation_time", "creator", "deadline", "depends_on",
    "dupe_of", "estimated_time", "groups", "id", "is_confirmed",
    "is_open", "keywords", "last_change_time", "op_sys", "platform",
    "priority", "product", "qa_contact", "remaining_time", "resolution",
    "see_also", "severity", "status", "summary", "target_milestone",
    "url", "version", "whiteboard", "quicksearch"]

FIELD_ALIAS = {
    'comment': 'longdesc'
}

ARRAY_FIELDS = {
    'blocks': {
        'prefix': ['+', '-', '='],
        'field': ['add', 'remove', 'set'],
        'type': int},
    'depends_on': {
        'prefix': ['+', '-', '='],
        'field': ['add', 'remove', 'set'],
        'type': int},
    'keyword': {
        'prefix': ['+', '-', '='],
        'field': ['add', 'remove', 'set'],
        'type': str},
    'alias': {
        'prefix': ['+', '-'],
        'field': ['add', 'remove'],
        'type': str},
    'see_also': {
        'prefix': ['+', '-'],
        'field': ['add', 'remove'],
        'type': str},
    'groups': {
        'prefix': ['+', '-'],
        'field': ['add', 'remove'],
        'type': str},
    'cc': {
        'prefix': ['+', '-'],
        'field': ['add', 'remove'],
        'type': str}}

NESTED_FIELDS = {
    'comment':
        {'field': 'body'}}

OPTIONS = {
    'url': {},
    'insecure': {'default': False, 'type': bool},
    'use_keyring': {'default': False, 'type': bool},
    'yaml_output': {'default': False, 'type': bool},
    'username': {},
    'password': {},
    'token': {},
    'api_key': {},
    'show_field_names': {'default': DEFAULT_FIELDS}}


class folded_unicode(unicode):
    pass


class literal_unicode(unicode):
    pass


def folded_unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')


def literal_unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(folded_unicode, folded_unicode_representer)
yaml.add_representer(literal_unicode, literal_unicode_representer)


class Options(object):
    def __init__(self, fields, config, args):
        for f, v in fields.iteritems():
            if hasattr(args, f) and getattr(args, f) is not None:
                setattr(self, f, getattr(args, f))
            elif config.has_option('core', f):
                if v.get('type') == bool:
                    setattr(self, f, config.getboolean('core', f))
                elif v.get('type') == int:
                    setattr(self, f, config.getint('core', f))
                elif v.get('type') == float:
                    setattr(self, f, config.getfloat('core', f))
                else:
                    setattr(self, f, config.get('core', f))
            else:
                setattr(self, f, v.get('default'))


def print_error(msg):
    sys.stderr.write("pybz: error: " + str(msg) + "\n")


def process_fields(fields, valid_fields, array_fields={},
                   nested_fields={}, field_alias={}):
    params = {}
    if fields:
        valid_fields = [f.lower() for f in valid_fields]
        for field in fields:
            name = field.split(":")[0].lower()
            value = (":".join(field.split(":")[1:])).strip()
            if name in field_alias:
                name = field_alias[name]
            if name in valid_fields:
                if name in array_fields:
                    try:
                        prefix = array_fields[name]['prefix']
                        idx = map(value.startswith, prefix).index(True)
                        value = value[len(prefix[idx]):]
                        value = array_fields[name]['type'](value)
                        field = array_fields[name]['field'][idx]
                        if name not in params:
                            params[name] = {}
                        if field not in params[name]:
                            params[name][field] = []
                        params[name][field].append(value)
                    except:
                        raise Exception("Field '%s' must start with '%s'"
                                        % (name, ",".join(prefix)))
                elif name in nested_fields:
                    subname = nested_fields[name]['field']
                    params[name] = {}
                    params[name][subname] = value
                else:
                    if name in params:
                        if isinstance(params[name], list):
                            params[name].append(value)
                        else:
                            params[name] = list([params[name], value])
                    else:
                        params[name] = value
            else:
                raise Exception("Invalid field name '%s'" % name)
    return params


def stringify(v):
    if isinstance(v, list):
        return ", ".join(map(stringify, v))
    elif isinstance(v, unicode):
        return v.encode('ascii', 'replace')
    else:
        return str(v)


def print_bug(b, output_fields, yaml_output=False):
    if not yaml_output:
        fields = []
        for f in output_fields:
            if f in b:
                fields.append(stringify(b[f]))
        print " ".join(fields)
    else:
        obj = dict((f, b[f]) for f in output_fields if f in b)
        sys.stdout.write(yaml.safe_dump(obj, explicit_end=True,
                         default_flow_style=False, width=70))


def create_argparser():
    parser = argparse.ArgumentParser(
        prog='pybz',
        description=meta.DESCRIPTION,
        epilog="Full documentation here: https://github.com/acornejo/pybz")
    parser.add_argument('--version', '-V', action='version',
                        version='%(prog)s v' + meta.VERSION)
    parser.add_argument('--url', action='store', type=str,
                        default=None, help='bugzilla server http url')
    parser.add_argument('--username', '-u', action='store', type=str,
                        default=None, help='bugzilla username')
    parser.add_argument('--password', '-p', action='store', type=str,
                        default=None, help='bugzilla password')
    parser.add_argument('--token', '-t', action='store', type=str,
                        default=None, help='bugzilla token')
    parser.add_argument('--api-key', action='store', type=str,
                        dest='api_key', default=None, help='bugzilla API key')
    parser.add_argument('--insecure', '-k', action='store_true',
                        dest='insecure', default=None,
                        help='allow insecure SSL certificate')
    parser.add_argument('--use-keyring', '-K', action='store_true',
                        dest='use_keyring', default=None,
                        help='use keyring to store/retrieve password')

    subparser = parser.add_subparsers(dest='command', metavar='COMMAND')

    new_parser = subparser.add_parser('new', help='create new bug')
    new_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
                            nargs='+', required=True, action='store',
                            default=None, help='field(s) to be set')

    get_parser = subparser.add_parser('get', help='get bug information')

    get_parser.add_argument('-n', '--bugnum', metavar='BUGNUM',
                            type=int, dest='bugnum', nargs='+',
                            action='store', default=None,
                            help='bug number(s)')
    get_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
                            nargs='+', action='store', default=None,
                            help='field(s) used for search')
    get_parser.add_argument('-s', '--show-field-names', metavar='NAME',
                            type=str, nargs='+', action='store',
                            default=None, dest='show_field_names',
                            help='list of the names of the fields to return')
    get_parser.add_argument('--yaml-output', '-y', action='store_true',
                            dest='yaml_output', default=False,
                            help='output in yaml format')

    set_parser = subparser.add_parser('set', help='set bug information')
    set_parser.add_argument('-n', '--bugnum', metavar='BUGNUM',
                            type=int, dest='bugnum', nargs='+',
                            action='store', required=True, default=None,
                            help='bug number(s)')
    set_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
                            nargs='+', required=True, action='store',
                            default=None, help='field(s) to be set')

    subparser.add_parser('list-fields', help='list all available bug fields')
    subparser.add_parser('list-products',
                         help='list all available bug products')
    component_parser = subparser.add_parser(
        'list-components',
        help='list all components for a given product')
    component_parser.add_argument('product', default=None, type=str,
                                  help='product name')

    return parser


def main(cmd_args=None):
    # Argument parser
    argparser = create_argparser()
    args = argparser.parse_args(cmd_args)

    if args.command == 'get':
        if args.bugnum is None and args.fields is None:
            argparser.error('one of the arguments -n/--bugnum '
                            '-f/--fields is required')
        elif args.bugnum is not None and args.fields is not None:
            argparser.error('argument -n/--bugnum not allowed with'
                            'argument -f/--fields')

    # Config parser
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)

    # Get options from config and args
    opts = Options(OPTIONS, config, args)

    # Get password through keyring or stdin
    if not opts.api_key and not opts.token:
        use_login = True
        if opts.username is not None:
            if opts.password is None:
                if opts.use_keyring:
                    opts.password = keyring.get_password('pybz', opts.username)
                if opts.password is None:
                    if sys.stdin.isatty():
                        print "Username: ", opts.username
                        opts.password = getpass.getpass()
            if opts.password is None or opts.password == "":
                print_error('Cannot login without password')
                return 1
            elif opts.use_keyring:
                keyring.set_password('pybz', opts.username, opts.password)
    else:
        use_login = False

    try:
        # Create API connection
        api = rest.API(opts.url, opts.insecure, opts.token, opts.api_key)

        # Login if appropriate
        if use_login:
            api.login(opts.username, opts.password)

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
            params = {}
            if args.bugnum:
                params['id'] = args.bugnum
            params.update(process_fields(args.fields,
                          set(GETTING_FIELDS + api.list_fields()),
                          field_alias=FIELD_ALIAS))
            for b in api.bug_get(params):
                print_bug(b, opts.show_field_names, opts.yaml_output)
        elif args.command == 'set':
            params = {'ids': args.bugnum}
            params.update(process_fields(args.fields,
                          set(SETTABLE_FIELDS + api.list_fields()),
                          ARRAY_FIELDS, NESTED_FIELDS))
            for b in api.bug_set(params):
                print b['id']
        elif args.command == 'new':
            params = process_fields(args.fields,
                                    set(CREATING_FIELDS + api.list_fields()))
            for f in MANDATORY_FIELDS:
                if f not in params:
                    print_error("Missing mandatory field '%s'" % f)
                    return 1
            b = api.bug_new(params)
            print b['id']

        if use_login:
            api.logout()
    except Exception as inst:
        print_error(inst)
        if use_login:
            api.logout()
        return 1

    return 0
