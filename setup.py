from donfig import __version__
from distutils.core import setup
from setuptools.config import read_configuration

setup(name='donfig',
    version=__version__,
    description='Nicer config writing',
    long_description_content_type='text/markdown',
    author='Hugh Ramsden',
    url='https://github.com/0Hughman0/donfig',
    download_url="https://github.com/0Hughman0/donfig/archive/{}.tar.gz".format(__version__),
    py_modules=['donfig'],
    license='MIT',
    python_requires=">=3.4")

conf_dict = read_configuration('./setup.cfg')
