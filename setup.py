# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()
with open(path.join(here, 'config/requirements.txt'), encoding='utf-8') as f:
    requirements = [req.trim() for req in f.read().split("\n")]

setup(
    name='rscraper',
    version='0.1.0',

    description='Scrape information about R projects from Github',
    long_description=long_description,

    url='https://github.com/cbogart/rscraper',
    author='Chris Bogart',
    author_email='cbogartdenver@gmail.com',
    license='Apache2',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: Apache',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='sample setuptools development',
    packages=['rscraper'],
    install_requires=requirements
)
