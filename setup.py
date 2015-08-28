from setuptools import setup
import pybz.meta as meta

readme = '\n' + open('README.md').read()

setup(
    author=meta.AUTHOR,
    author_email=meta.EMAIL,
    name=meta.NAME,
    version=meta.VERSION,
    license=meta.LICENSE,
    url=meta.URL,
    description=meta.DESCRIPTION,
    long_description=readme,
    platforms=['all'],
    packages=['pybz'],
    install_requires=['keyring', 'requests'],
    entry_points={
        'console_scripts': [
            'pybz = pybz.cmd:main',
        ]
    }
)
