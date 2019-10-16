import setuptools

from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip

from aidockermon import __version__


def read_requirements_txt(default=[]):
    with io.open('requirements.txt', 'r') as f:
        r = f.read().split()
    return r if r else default


pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile['packages'], r=False)
test_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)


# entry points
entry_points = {
    'console_scripts': [
        'aidockermon = aidockermon.aidockermon:main'
    ]
}


setuptools.setup(
    version=__version__,
    install_requires=requirements,
    test_require=test_requirements,
    entry_points=entry_points,
)
