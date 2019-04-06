import io
import os
import sys
import platform
import unittest
import setuptools

from aidockermon import __version__


def read_requirements_txt(default=[]):
    with io.open('requirements.txt', 'r') as f:
        r = f.read().split()
    return r if r else default


tests_require = []

install_requires = []

dependency_links = []


requirements_txt = read_requirements_txt()
install_requires.extend(requirements_txt)


# entry points
entry_points = {
    'console_scripts': [
        'aidockermon = aidockermon.aidockermon:main'
    ]
}


# test suite
def load_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', top_level_dir='./')
    return test_suite


setuptools.setup(
    version=__version__,
    tests_require=tests_require,
    install_requires=install_requires,
    dependency_links=dependency_links,
    test_suite="setup.load_test_suite",
    entry_points=entry_points
)
