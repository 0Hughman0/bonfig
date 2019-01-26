from bonfig import __version__
from distutils.core import setup
from setuptools.config import read_configuration


setup(name='bonfig',
    version=__version__,
    description="Don't write configurations, write class declarations.",
    long_description_content_type='text/markdown',
    author='Hugh Ramsden',
    url='https://github.com/0Hughman0/bonfig',
    download_url="https://github.com/0Hughman0/bonfig/archive/{}.tar.gz".format(__version__),
    py_packages=['bonfig', 'bonfig.fields'],
    license='MIT',
    python_requires=">=3.4",
    test_requires="pytest")

conf_dict = read_configuration('./setup.cfg')
