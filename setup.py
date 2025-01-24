#!/usr/bin/env python3

'''
ESMF TestKit (esmftk)

Copyright (c) 2002-2025 University Corporation for Atmospheric Research, Massachusetts Institute of Technology, Geophysical Fluid Dynamics Laboratory, University of Michigan, National Centers for Environmental Prediction, Los Alamos National Laboratory, Argonne National Laboratory, NASA Goddard Space Flight Center. All rights reserved.
'''

from setuptools import setup

setup(
    name='esmftk',
    version='1.0.0',
    license='UIUC',
    description='ESMF TestKit is a Python based testing framework for ESMF',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/esmf-org/esmf-testkit',
    author='ESMF Core Team',
    author_email='esmf_support@ucar.edu',
    install_requires=[
        'PyYAML',
    ],
    packages=['esmftk'],
    package_data={
        'esmftk': [
            'esmftk/*',
        ]
    },
    platforms=['Mac', 'Linux'],
    classifiers=[
        'License :: OSI Approved :: University of Illinois/NCSA Open Source License',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    keywords=[
        'ESMF',
        'Earth System Modeling Framework',
        'testkit',
        'testing framework'
    ],
    entry_points={
        'console_scripts': [
            'esmftk = esmftk.__main__:main',
        ]
    }
)
