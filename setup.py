# -*- coding: utf-8 -*-
"""
Setup.py file
"""
import io
import os
import sys
import re
from setuptools import setup, find_packages, Command

AUTHOR = 'Frost Ming'
EMAIL = 'mianghong@gmail.com'
URL = 'https://github.com/frostming/marko'

NAME = 'marko'
DESCRIPTION = 'A markdown parser with high extensibility.'
REQUIRES_PYTHON = ">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*"
REQUIRES = [
    'backports.html;python_version<"3.4"'
]

here = os.path.dirname(__file__)
readme = io.open(os.path.join(here, 'README.md'), encoding='utf-8').read()
about = io.open(os.path.join(here, 'marko', '__init__.py'), encoding='utf-8').read()
VERSION = re.findall(r'^__version__ *= *(.+?) *$', about, re.M)[0][1:-1]


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            from shutil import rmtree
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(VERSION))
        os.system('git push --tags')

        sys.exit()


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=readme,
    long_description_content_type='text/markdown',
    install_requires=REQUIRES,
    python_requires=REQUIRES_PYTHON,
    extras_require={'toc': ['python-slugify']},
    include_package_data=True,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    license='MIT',
    packages=find_packages(exclude=('tests', 'tests.*')),
    cmdclass={
        'upload': UploadCommand
    },
    entry_points={'console_scripts': ['marko = marko.cli:main']},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        'Operating System :: OS Independent',
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
)
