#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 13:36 BRT 2020

author: guilherme passos | twitter: @gpass0s
"""
from setuptools import find_packages
from setuptools import setup


setup(
    name="isales",
    version="0.0.0",
    description="Isales is an automated service that predicts leads probability to close",
    author="@gpass0s",
    url="https://github.com/gPass0s/isales",
    packages=find_packages(exclude=["tests*"]),
)
