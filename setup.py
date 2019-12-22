#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import cli_translate

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='cli_translate',
    version=cli_translate.__version__,
    packages=find_packages(),
    install_requires=['pyperclip>=1.5.27', 'requests>=2.18', 'pyquery>=1.2.9'],
    description='Useful translation tool for console. With features: translate text from clipboard and store translation logs',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Insolita',
    author_email='webmaster100500@ya.ru',
    url='https://github.com/Insolita/cli_translate',
    download_url='https://github.com/Insolita/cli_translate/tarball/master',
    license='MIT',
    keywords='translation, translate, yandex, google, google translate, clipboard, notify-send, console',
    classifiers=[
        'Programming Language :: Python :: 3',
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.4',
    entry_points={
        'console_scripts': [
            'itrans = cli_translate.core:main'
        ]
    },
)
