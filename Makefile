all:

.PHONY: clean virtualenv pip dist install test

test:
	env/bin/pip install -r dev-requirements.txt
	env/bin/flake8 setup.py pybz/*.py test/*.py
	env/bin/python -m unittest discover

upload: dist
	env/bin/pip install -r dev-requirements.txt
	env/bin/twine upload dist/*.tar.gz

build: env
	env/bin/python setup.py build

dist: env
	pandoc README.md --from markdown --to rst -s -o README.rst
	env/bin/python setup.py sdist

install: env
	env/bin/python setup.py install

env: virtualenv
	@test -d env || ( virtualenv env && env/bin/pip install -r requirements.txt )

virtualenv: pip
	@hash virtualenv || sudo pip install virtualenv

pip:
	@hash pip || ( curl --silent --show-error https://bootstrap.pypa.io/get-pip.py | sudo python )

clean:
	rm -fr env pybz/*.pyc build dist *.egg-info README.rst
