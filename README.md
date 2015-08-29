# pybz

pybz provides a  simple command line utility to interact with a bugzilla
5.x server through their REST API. The specification of the bugzilla
REST API is
[documented here](http://bugzilla.readthedocs.org/en/latest/api/index.html).

# Installation

The recommended installation method is through `pip`. Installing as root
with pip is not recommended since it might create conflicts with other
globally installed python packages.

    pip install --user pybz

This will install pybz in `~/.local/bin`.

If your system doesn't have `pip` available, you can install it as
follows:

	curl --silent --show-error https://bootstrap.pypa.io/get-pip.py | sudo python

# Configuration

No configuration is required to use pybz, all parameters can be
specified in the command line. The server URL can be specified with the
`--url` flag; a server URL is required to perform any operation on
bugzilla. For operations that require authentication you must also
specify a username, which can also be provided in the command-line with
the `--username` flag.

To avoid having to specify the server URL and the username on every
invocation of `pybz`, these and other settings can be stored in an
initialization file stored at `~/.pybz`.

Example `~/.pybz` file:

    [core]
    url = bugzilla.mozilla.org
    username = alice@pybz.org
    use_keyring = True
    insecure = False

Although possible, it is discouraged to store the password in the
initialization file or to provide it through the command-line.
When a username is specified but no password is provided, it will be
requested through the standard input. If the `use_keyring` option is
enabled, passwords will be securely stored and retrieved using the
system keyring.

# Usage

Use the `-h` or `--help` flags to get information about all the
calling options. pybz supports the following commands

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
simply enter a list of numeric bug id's to retrieve from the server.

You can also use fields to create more complex queries. Fields must be
of the form `name:value`, if your value must contain spaces then you
must quote the whole field as follows `"name:value with spaces"`.

When searching different field names are searched as an AND,
and if the same field name appears multiple times then it is used as an
OR. So searching for "priority:P1 priority:P2" returns all bugs of
priority P1 OR P2, while searching for "status:OPEN priority:P1" returns
bugs of with an OPEN status AND priority P1.

Performing OR operations across different fields is not supported (for
instance, if you wanted to find all bugs which have either a
status OPEN or are have priority P1). For this you can use the
quicksearch field, and follow the
[quicksearch API](https://bugzilla.mozilla.org/page.cgi?id=quicksearch.html)

## Updating bugs

Updating bugs uses the same field syntax as searching. The only
difference is that some fields are treated specially, in particular the
fields `blocks`, `depends_on`, `see_also`, `groups`, `cc` and
`keywords`. This is because these fields do not contain a single value,
but instead contain an array of values.

If you want to specify that a is blocked by bug 12345 and 12346 then you
would do `blocks:=12345 blocks:=12346`. If instead you wanted to add bug
12346 to the list of blocking bugs, then you would use `blocks:+12346`,
and if you wanted to remove bug 12346 from the blocking list you
would use `blocks:-12346`.

All array like fields support the `+` and `-`, but not all of them
support setting with the `=` operator. This is a limitation of the
bugzilla API and not bugz. To see which fields support it simply try it
out and pybz will notify you of unsupported operations.

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

Add charlie@pybz.org to the CC list of bug 12345, and remove
alice@pybz.org from the CC list.

    pybz set -n 12345 -f cc:+charlie@pybz.org cc:-alice@pybz.org

Report a new bug

    pybz new -f "summary:new and terrible bug" product:pybz priority:P2 assigned_to:alice@pybz.org

## Advanced

Reassign all bugs from bob@pybz.org to charlie@pybz.org

    pybz get -f assigned_to:bob@pybz.org -s id | xargs pybz set -f assigned_to:charlie@pybz.org -n

Display a list of developers sorted by the number of open P1 bugs assigned to
them

    pybz get -f priority:P1 status:OPEN -s asigned_to | sort | uniq -c | sort
