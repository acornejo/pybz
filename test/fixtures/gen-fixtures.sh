#!/bin/bash

# __init__.py must be modified if this script is updated

REST_URL="https://landfill.bugzilla.org/bugzilla-5.0-branch/rest"
PROD_NAME="WorldControl"
BUG1="12341"
BUG1="12342"

curl -o products.json ${REST_URL}/product?type=accessible
curl -o fields.json ${REST_URL}/field/bug
curl -o components.json ${REST_URL}/product?names=${PROD_NAME}
curl -o bug1.json ${REST_URL}/bug?id=${BUG1}
curl -o bug2.json ${REST_URL}/bug?id={$BUG2}
