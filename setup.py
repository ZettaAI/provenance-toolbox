import sys
import setuptools
from setuptools import setup, find_packages


__version__ = "0.0.1"


setup(
    name='provenance-tools',
    version=__version__,
    description='Processing voxelwise descriptors for Connectomics.',
    author='Nicholas Turner',
    author_email='nturner@zetta.ai',
    url='https://github.com/ZettaAI/provenance-tools',
    packages=setuptools.find_packages()
)
