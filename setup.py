# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='clg-logger',
    version='0.1.0',
    author='François Ménabé',
    author_email='francois.menabe@gmail.com',
    url = 'https://clg.readthedocs.org/en/latest/',
    download_url = 'http://github.com/fmenabe/python-clg-logger',
    license='MIT License',
    description='Manage logging based on command-line options.',
    long_description=open('README.rst').read(),
    keywords=['command-line', 'argparse', 'wrapper', 'clg', 'logging'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities'
    ],
    py_modules=['clg/logger.py'],
    install_requires=['clg'])
