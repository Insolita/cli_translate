#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import cli_translate

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name     = 'cli_translate',
    version  = cli_translate.__version__,
    packages = find_packages(),
    requires = ['python (>= 3.0)', 'pyperclip (>= 1.5.27)', 'requests(>=2.18, <=3.0.0)', 'pyquery(>=1.2.9)'],
    description  = 'Useful translation tool for console. With features: translate text from clipboard and store translation logs',
    long_description = long_description, 
    author       = 'Insolita',
    author_email = 'webmaster100500@ya.ru',
    url          = 'https://github.com/insolita/cli-translate',
    download_url = 'https://github.com/insolita/cli-translate/tarball/master',
    license      = 'MIT License',
    keywords     = 'translation, translate, yandex, google, google translate, clipboard, notify-send, console',
    classifiers  = [
        'Programming Language :: Python :: 3',
    ],
    entry_points={
          'console_scripts': [
              'itranslate = cli_translate.core:main'
          ]
},
)