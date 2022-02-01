import sys
import setuptools
from setuptools import setup, find_packages


__version__ = "0.1.0"


setup(
    name='provenancetoolbox',
    version=__version__,
    description=('Some basic utilities to standardize the use'
                 ' of CloudVolume provenance files'),
    author='Nicholas Turner',
    author_email='nturner@zetta.ai',
    url='https://github.com/ZettaAI/provenancetoolbox',
    packages=setuptools.find_packages(),
    install_requires=['GitPython>=3.1.26', 'docker>=5.0.3',
                      'cloud-volume']
)
