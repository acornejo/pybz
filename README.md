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

get options:
    --show-fields|-s field1,field2
    --extra-fields|-e field1,field2
