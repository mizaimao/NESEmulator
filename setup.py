#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="nsim",
    version="0.1",
    description="Python implementation of NES simulator.",
    author="Mizaimao",
    packages=find_packages(include=["nsim", "nsim.*"]),
)
