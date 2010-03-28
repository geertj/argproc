#
# This file is part of ArgProc. ArgProc is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# ArgProc is copyright (c) 2010 by the ArgProc authors. See the file
# "AUTHORS" for a complete overview.

import os
from setuptools import setup, Extension, Command


class gentab(Command):
    """Generate the PLY parse tables."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from argproc.parser import RuleParser
        RuleParser._write_parsetab()


setup(
    name = 'argproc',
    version = '1.1',
    description = 'A rule-based arguments processor',
    author = 'Geert Jansen',
    author_email = 'geert@boskant.nl',
    url = 'http://bitbucket.org/geertj/argproc',
    license = 'MIT',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules' ],
    package_dir = {'': 'lib'},
    packages = ['argproc', 'argproc.test'],
    test_suite = 'nose.collector',
    cmdclass = { 'gentab': gentab },
    install_requires = ['ply >= 3.3']
)
