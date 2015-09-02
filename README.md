# pybz

pybz provides a  simple command line utility to interact with a bugzilla
5.x server through their REST API. The specification of the bugzilla
REST API is
[documented here](http://bugzilla.readthedocs.org/en/latest/api/index.html).

*Why?* Short answer: necessity. I need to use bugzilla at work, I
dislike the web interface, and every other tool I looked at would either
refuse to authenticate with our server (perhaps because they use the now
deprecated XMLRPC endpoint), or lack a feature I needed. Thus, `pybz` came
to be as yet-another alternative to interact with bugzilla without using
a web browser.

# Installation

The recommended installation method is through `pip`. Installing as root
with pip might create conflicts with other globally installed python
packages (I am looking about you `requests`); therefore I recommend with
pip on your user folder.

    pip install --user pybz

This will install `pybz` in `~/.local/bin`.

If your system doesn't have `pip` available, you can install it as
follows:

	curl --silent --show-error https://bootstrap.pypa.io/get-pip.py | sudo python

# Configuration

No configuration is required to use `pybz`, all parameters can be
specified in the command line. A server URL is required to perform any
operation on bugzilla, and can be specified with the `--url` flag. For
operations that require authentication you must also specify a username,
which can also be provided in the command line with the `--username`
flag.

To avoid having to specify the server URL and the username on every
invocation of `pybz`, these and other settings can be stored in a
per-user configuration file stored at `~/.pybz`.

Example `~/.pybz` file:

    [core]
    url = bugzilla.mozilla.org
    username = alice@pybz.org
    use_keyring = True
    insecure = False

Although possible, it is discouraged to store the password in the
initialization file or to provide it through the command line.
When a username is specified but no password is provided, it will be
requested through the standard input. If the `use_keyring` option is
enabled, passwords will be securely stored and retrieved using the
system keyring.

# Usage

Use the `-h` or `--help` flags to get information about all the
calling options. `pybz` supports the following commands

command          |   description
-----------------|------------------------------------------
new              |   create new bug
get              |   get bug information
set              |   set bug information
list-fields      |   list all available bug fields
list-products    |   list all available bug products
list-components  |   list all components for a given product

Commands like `new`, `get` and `set` accept fields as parameters.

## Creating bugs

When creating new bugs the fields `product`, `component`, `version` and
`summary` are mandatory, all other fields are optional. Fields which
accept a list of values like `cc` can be populated by specifying each
value individual, i.e. `cc:alice@pybz.org cc:bob@pybz.org`, much like
searching.

## Searching for bugs

The `get` command is used to search for bugs, in the simplest form you
use the `-n` flag specify a list of numeric bug id's to be retrieved
from the server.

Bugs can also be retrieved using field queries using the `-f` flag.
Fields must be of the form `name:value`, if your value must contain
spaces then you must quote the whole field as follows `"name:value with
spaces"`.

When multiple field queries on the different field name are searched
using an AND operation, and field queries on the same field name are
searched using an OR operation. For instance, searching for "priority:P1
priority:P2" returns all bugs of priority P1 OR P2, while searching for
"status:OPEN priority:P1" returns bugs of with an OPEN status AND
priority P1.

Performing OR operations across different fields is not supported (for
instance, if you wanted to find all bugs which have either a
status OPEN or are have priority P1). This is not a limitation imposed
by `pybz` but simply the specification of the bugzilla REST API. For more
complex queries you can use the quicksearch field, and follow the
[quicksearch API](https://bugzilla.mozilla.org/page.cgi?id=quicksearch.html)

## Updating bugs

Updating bugs uses the same field syntax as searching. Fields do not
contain a single value but a list of values require different syntax.
Specifically, the fields `blocks`, `depends_on`, `see_also`, `groups`,
`cc` and `keywords` require using an extended syntax using the `+` to
add values to the array, `-` to remove values from the array and `=` to
replace the values in the array with new ones.

If you want to specify that a is blocked by bug 12345 and 12346 then you
would do `blocks:=12345 blocks:=12346`. If instead you wanted to add bug
12346 to the list of blocking bugs, then you would use `blocks:+12346`,
and if you wanted to remove bug 12346 from the blocking list you
would use `blocks:-12346`.

All array like fields support the `+` and `-`, but not all of them
support setting with the `=` operator. This reflects supported
operations by the bugzilla API and not a choice made in `pybz` To see
which fields support it simply try it out and `pybz` will notify you of
unsupported operations.

# Examples

In the interest of succinctness, the examples below omit the bugzilla
URL as well as the username. The configuration section of this document
provides more details on these options.

## Basic

Get info about bug number 12345

    pybz get -n 12345

Get info about bug numbers 12345, 12346 and 12347

    pybz get -n 12345 12346 12347

Search for all bugs assigned to alice@pybz.org

    pybz get -f assigned_to:alice@pybz.org

Search for all bugs assigned to alice@pybz.org with priority P1

    pybz get -f assigned_to:alice@pybz.org priority:P1

Search for all open bugs with priority P1 or P2

    pybz get -f status:OPEN priority:P1 priority:P2

(Re-)assign bug number 12345 to bob@pybz.org and make it a P2

    pybz set -n 12345 -f assigned_to:bob@pybz.org priority:P2

Upgrade bug number 12345 to have priority P1

    pybz set -n 12345 -f priority:P1

Report a new bug

    pybz new -f "summary:new and terrible bug" product:pybz priority:P2 assigned_to:alice@pybz.org

## Advanced

Add charlie@pybz.org to the CC list of bug 12345, remove
alice@pybz.org from the CC list, and add a comment describing the
change (all in one command!).

    pybz set -n 12345 -f cc:+charlie@pybz.org cc:-alice@pybz.org "comment:adding charlie to the discussion, and removing alice"

Reassign all bugs from bob@pybz.org to charlie@pybz.org

    pybz get -f assigned_to:bob@pybz.org -s id | xargs pybz set -f assigned_to:charlie@pybz.org -n

Display a list of developers sorted by the number of open P1 bugs assigned to
them

    pybz get -f priority:P1 status:OPEN -s asigned_to | sort | uniq -c | sort

# Troubleshooting

## pybz hangs

The python keyring has been known to hang on systems where no keyring
can be found. To prevent this, simply disable the `use_keyring` option
in the `pybz` configuration file, and do not specify this option in the
command line. To see if this is your problem, open up a python console
and import the keyring module.

    $ python
    Python 2.7.10 (default, Jul 13 2015, 12:05:58)
        [GCC 4.2.1 Compatible Apple LLVM 6.1.0 (clang-602.0.53)] on darwin
        Type "help", "copyright", "credits" or "license" for more
        information.
    >>> import keyring
