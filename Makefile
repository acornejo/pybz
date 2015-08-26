all: env

env:
	virtualenv env
	. env/bin/activate && pip install -r requirements.txt

clean:
	rm -fr env
	rm -f pybz/*.pyc
