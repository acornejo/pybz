import meta
import rest
import keyring
import getpass
import textwrap
import ConfigParser
import argparse
import sys
import os

CONFIG_FILE = os.path.expanduser('~/.pybz')
MARGIN=70
INDENT=4

MANDATORY_FIELDS = ["product", "component", "summary", "version"]

DEFAULT_FIELDS = ["id", "status", "priority", "summary"]

SETTABLE_FIELDS = ["alias", "assigned_to", "blocks", "depends_on", "cc",
    "comment", "component",   "deadline", "dupe_of", "estimated_time",
    "groups", "keywords", "op_sys","platform", "priority", "product",
    "qa_contact", "reset_assigned_to", "reset_qa_contact", "resolution",
    "see_also", "status", "summary", "target_milestone", "url",
    "version", "whiteboard"]

CREATING_FIELDS = ["product", "component", "summary", "version",
    "description", "op_sys", "platform", "priority", "severity",
    "alias", "assigned_to", "cc", "groups", "qa_contact", "status",
    "resolution", "target_milestone"]

GETTING_FIELDS = ["alias", "assigned_to", "blocks", "cc",
    "classification", "component",          "creation_time", "creator",
    "deadline", "depends_on", "dupe_of", "estimated_time", "groups",
    "id", "is_confirmed", "is_open", "keywords", "last_change_time",
    "op_sys", "platform", "priority", "product", "qa_contact",
    "remaining_time", "resolution", "see_also", "severity", "status",
    "summary", "target_milestone", "url", "version", "whiteboard"]

SPECIAL_FIELDS = {
    'blocks': {'prefix': ['+', '-','='], 'field': ['add', 'remove','set'], 'type': int},
    'depends_on': {'prefix': ['+', '-','='], 'field': ['add', 'remove','set'],  'type': int},
    'keyword': {'prefix': ['+', '-','='], 'field': ['add', 'remove','set'], 'type': str},
    'alias': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
    'see_also': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
    'groups': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
    'cc': {'prefix': ['+', '-'], 'field': ['add', 'remove'], 'type': str},
    'comment': {'field': 'body'}}

OPTIONS = {
    'url': {},
    'insecure': {'default': False, 'type': bool},
    'use_keyring': {'default': False, 'type': bool},
    'block': {'default': False, 'type': bool},
    'username': {},
    'password': {},
    'token': {},
    'show_fields': {'default': DEFAULT_FIELDS} }

class Options(object):
    def __init__(self, fields, config, args):
        for f, v in fields.iteritems():
            if hasattr(args, f) and getattr(args, f) is not None:
                setattr(self, f, getattr(args, f))
            elif config.has_option('core', f):
                if v.get('type') == bool:
                    setattr(self, f, config.getboolean('core', f))
                else:
                    setattr(self, f, config.get('core', f))
            else:
                setattr(self, f, v.get('default'))

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
                    if name in params:
                        if isinstance(params[name], list):
                            params[name].append(value)
                        else:
                            params[name] = list(params[name], value)
                    else:
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
                        subname = extra_processing['field']
                        params[name] = {}
                        params[name][subname] = value
            else:
                raise Exception ("Invalid field name '%s'"%name)
    return params

def print_block(prefix, text):
    width = MARGIN-len(prefix)
    lines = textwrap.wrap(text, width)
    for line in lines:
        print prefix + line

def print_bug(b, output_fields, block=False):
    if not block:
        fields = []
        for f in output_fields:
            if f in b:
                if isinstance (b[f], list):
                    fields.append(",".join(map(str, b[f])))
                else:
                    fields.append(str(b[f]))
        print " ".join(fields)
    else:
        for v in output_fields:
            if v not in b: continue
            f = b[v]
            if not isinstance(f, list):
                line = '%s: %s'%(v, str(f))
                if len(line) < MARGIN:
                    print line
                else:
                    print "%s: >"%v
                    print_block(' '*INDENT, str(f))
            else:
                line = '%s: %s'%(v, ", ".join(map(str, f)))
                if len(line) < MARGIN:
                    print line
                else:
                    print "%s:"%v
                    for sf in f:
                        line = ' '*INDENT + " - %s"%str(sf)
                        if len(line) < MARGIN:
                            print line
                        else:
                            print ' '*INDENT + "- >"
                            print_block(' '*(INDENT*2), str(sf))
        print "---"


def main():
    # Argument parser
    parser = argparse.ArgumentParser(description=meta.DESCRIPTION + " " + meta.VERSION,
            epilog = "For more documentation go here: https://github.com/acornejo/pybz")
    parser.add_argument('--url', action='store', type=str,
            default=None, help='bugzilla server http url')
    parser.add_argument('--username', '-u', action='store', type=str,
            default=None, help='bugzilla username')
    parser.add_argument('--password', '-p', action='store', type=str,
            default=None, help='bugzilla password')
    parser.add_argument('--token', '-t', action='store', type=str,
            default=None, help='bugzilla token')
    parser.add_argument('--insecure', '-k', action='store_true', dest='insecure',
            default=False, help='allow insecure SSL certificate')
    parser.add_argument('--use-keyring', '-K', action='store_true', dest='use_keyring',
            default=None, help='use keyring to store/retrieve password')

    subparser = parser.add_subparsers(dest='command', metavar='COMMAND')

    new_parser = subparser.add_parser('new', help='create new bug')
    new_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
            nargs='+', required=True, action='store', default=None,
            help='fields to be set')

    get_parser = subparser.add_parser('get', help='get bug information')
    get_parser.add_argument('bugnum', type=int, nargs='*', help='bug number')
    get_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
            nargs='+', action='store', default=None,
            help='fields used for search')
    get_parser.add_argument('-s', '--show-fields', metavar='FIELD', type=str,
            nargs='+', action='store', default=None, dest='show_fields',
            help='fields to return (default: id status priority summary)')
    get_parser.add_argument('--block-output', '-b',
            action='store_true', dest='block', default=False,
            help='use block format output')

    set_parser = subparser.add_parser('set', help='set bug information')
    set_parser.add_argument('bugnum', type=int, nargs='+', help='bug number')
    set_parser.add_argument('-f', '--fields', metavar='FIELD', type=str,
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

    # Get options from config and args
    opts = Options (OPTIONS, config, args)

    # Get password through keyring or stdin
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


    try:
        # Create API connection
        api = rest.API(opts.url, opts.insecure, opts.token)

        # Login if appropriate
        if opts.username and opts.password:
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
            params.update(process_fields(args.fields, set(GETTING_FIELDS + api.list_fields())))
            for b in api.bug_get(params):
                print_bug (b, opts.show_fields, opts.block)
        elif args.command == 'set':
            params = {'ids': args.bugnum}
            params.update(process_fields(args.fields, set(SETTABLE_FIELDS + api.list_fields()), SPECIAL_FIELDS))
            for b in api.bug_set(params):
                print b['id']
        elif args.command == 'new':
            params = process_fields(args.fields, set(CREATING_FIELDS + api.list_fields()))
            for f in MANDATORY_FIELDS:
                if f not in params:
                    print_error("Missing mandatory field '%s'"%f)
            b = api.bug_new(params)
            print b['id']

        if opts.username and opts.password:
            api.logout()
    except Exception as inst:
        import traceback
        traceback.print_exc()
        print_error(inst)
        if opts.username and opts.password:
            api.logout()
        return 1

    return 0
