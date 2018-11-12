from bonfig import __version__
from distutils.core import setup
from setuptools.config import read_configuration

setup(name='bonfig',
    version=__version__,
    description='Nicer config writing',
    long_description_content_type='text/markdown',
    author='Hugh Ramsden',
    url='https://github.com/0Hughman0/bonfig',
    download_url="https://github.com/0Hughman0/bonfig/archive/{}.tar.gz".format(__version__),
    py_modules=['bonfig'],
    license='MIT',
    python_requires=">=3.4")

conf_dict = read_configuration('./setup.cfg')
