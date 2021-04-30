#!/usr/bin/env python
###############################################################################

from setuptools import setup

###############################################################################
###############################################################################

setup (
    name='avalanche-stakes',
    version='1.0.0',
    description='Avalanche stake concentration analysis',
    author='Hasan Karahan',
    author_email='avalanche@blackhan.com',
    url='https://github.com/hsk81/avalanche-stakes.git',
    install_requires=[
        'matplotlib>=3.4.1',
        'numpy>=1.20.2',
    ],
)

###############################################################################
###############################################################################
