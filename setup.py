#!/usr/bin/env python3

from setuptools import setup

exec(compile(open('clig/version.py').read(),'version.py','exec'))

setup(
    name                 = 'clig',
    author               = __author__,
    author_email         = __email__,
    version              = __version__,
    license              = __license__,
    url                  = 'https://shaw.cx/clig',
    description          = 'Command-Line GIT Server',
    long_description     = open('README.rst').read(),
    packages             = setuptools.find_packages(),
    include_package_data = True,
    zip_safe             = False,
    entry_points = {
        'console_scripts' : [
            'clig = clig:main',
            ]
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Version Control :: Git',
        ]
    )
