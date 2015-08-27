# pybz

pybz provides a  simple command line utility to interact with a bugzilla
5.x server through their REST API. The specification of the REST API
available from bugzilla is [documented here][restapi].

# Installation

The recommended installation method is through `pip`, namely:

    sudo pip install pybz

If your system doesn't have `pip` available, you can install it as
follows:

	curl --silent --show-error https://bootstrap.pypa.io/get-pip.py | sudo python

# Configuration

No configuration is required to use pybz, all parameters can be
specified in the command line.

To avoid having to specify the server url and the username (when using
authentication) on every invocation, pybz supports reading these
parameters from an initialization file stored at `~/.pybzrc`.

Example `~/.pybzrc` file:

    [core]
    url = bugzilla.mozilla.org
    username = alice@pybz.org
    use_keyring = True
    ssl_verify = True

The initialization file cannot store a password, and although the
password can be provided as a parameter in the command-line, this is
strongly discouraged. Instead, when a username is specified but no
password is provided, it will be requested through the standard input.
If the `use_keyring` option is enabled, passwords will be securely
stored in the system keyring.

# Basic Examples

Get info about bug 12345

    pybz get 12345

Search for all bugs assigned to alice@pybz.org

    pybz get -f assigned_to:alice@pybz.org

Search for all bugs assigned to alice@pybz.org with priority P1

    pybz get -f assigned_to:alice@pybz.org priority:P1

(Re-)assign bug 12345 to bob@pybz.org and make it a P2

    pybz set 12345 -f assigned_to:bob@pybz.org priority:P2

Upgrade bug 12345 to have priority P1

    pybz set 12345 -f priority:P1

Report a new bug

    pybz new -f "summary:new and terrible bug" product:pybz priority:P2
    assigned_to:alice@pybz.org

# Advanced Examples

Reassign all bugs from bob@pybz.org to charlie@pybz.org

    pybz get -f assigned_to:bob@pybz.org -s id | xargs pybz set -f assigned_to:charlie@pybz.org

Display a list of developers sorted by the number of open P1 bugs assigned to
them

    pybz get -f priority:P1 status:OPEN -s asigned_to | sort | uniq -c | sort

[restapi][http://bugzilla.readthedocs.org/en/latest/api/index.html]
