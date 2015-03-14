#!/usr/local/bin/python

## 
## Created by: Grant McGovern 
## Date: 18 July 2014 
## Purpose: Setup environment for WIN API.
## 

from setuptools import setup, find_packages

## Get our requirements from our .txt file
with open('requirements.txt') as requirements:
	modules = [line.strip('\n') for line in requirements]

setup(name = 'WIN',
	version = '1.0',
	description = 'A RESTful API service to WFU WIN',
	author = 'Grant McGovern, Gaurav Sheni',
	author_email = 'mcgoga12@wfu.edu',
	install_requires = modules
)
