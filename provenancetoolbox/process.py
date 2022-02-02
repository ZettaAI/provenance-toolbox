"""Storage of a processing step (process) along with its code environments.

Handles storing representations of a processing step that's produced or
modified a CloudVolume. These consist of a process description, code
environment, and a set of parameters.

Typical usage:
    description = 'Properly documenting a process'
    parameters = {'prudence': 10/10}
    code_env = PythonGithubEnv('.')  # path to a github repo directory

    process = Process(description, parameters, code_env)
    logprocess(cloudvolume, process)
"""
from __future__ import annotations

import os
import json
import pkg_resources
from typing import Union
from types import SimpleNamespace
from configparser import ConfigParser

import git
import cloudvolume as cv

from . import utils


__all__ = ['Process', 'PythonGithubEnv', 'DockerEnv',
           'logprocess', 'process_absent']


class CodeEnv:
    """A virtual class for representing a code environment

    Attributes:
        codeptr: Some type of "pointer" to use for determining the code
                 environment.
    """
    def __init__(self, codeptr: str):
        self.codeptr = codeptr

    def log(self) -> tuple[str, str]:
        """Preparing a CodeEnv for logging.

        Logging a code environment consists of specifying a "code environment
        file" that contains all of the required information to recover the
        environment. This method should collect that information from any
        subclass.

        Returns:
            Returns a tuple (filename, contents), where filename identifies
            the filename to store alongside the provenance file with
            detailed information about the code environment, and contents
            is a string that contains the contents of that file.
        """
        return self.filename, self.contents

    @property
    def filename(self):
        """The filename where we should store detailed information"""
        raise NotImplementedError

    @property
    def contents(self):
        """The detailed information to store in a code environment file"""
        raise NotImplementedError


class PythonGithubEnv(CodeEnv):
    """A code environment specified by a python github repository.

    Attributes:
        codeptr: A path to the root github directory of the repository.
        repo: A GitPython representation of the repository.
    """
    def __init__(self, codeptr: str):
        """Initialization.

        Creates the repo attribute from the codeptr argument.

        Arguments:
            codeptr: A path to the root github directory of the repository.
        """
        self.codeptr = codeptr
        self.repo = git.Repo(codeptr)

    @property
    def url(self) -> str:
        """The URL used to access the repository."""
        cfg = self.repo.config_reader()
        return cfg.get('remote "origin"', 'url')

    @property
    def repo_name(self) -> str:
        """The name of the github repository."""
        return repo_name_from_url(self.url)

    @property
    def commithash(self) -> str:
        """The hash of the current commit of the github repo."""
        return self.repo.commit().hexsha

    @property
    def diff(self) -> str:
        """The uncommitted code changes within the current environment."""
        return self.repo.git.diff()

    @property
    def packagelist(self) -> list[tuple[str, str]]:
        """The current environment of python packages"""
        return [(p.project_name, p.version)
                for p in pkg_resources.working_set]

    @property
    def filename(self) -> str:
        return f'{self.repo_name}_{self.commithash}'

    @property
    def contents(self) -> str:
        contents = dict()

        contents['name'] = self.url
        contents['CodeEnv type'] = 'PythonGithub'
        contents['commit hash'] = self.commithash
        contents['diff'] = self.diff
        contents['packages'] = self.packagelist

        return json.dumps(contents)


def repo_name_from_url(repo_url: str) -> str:
    """Extracts the bare repo-name from a URL.

    Args:
        repo_url: The URL used to access a github repository

    Returns:
        A string of the 'base' name of the repository.
    """
    return os.path.basename(repo_url).replace('.git', '')


class DockerEnv(CodeEnv):
    """A code environment specified by a docker image.

    Attributes:
        imagename: The userdefined name of the docker image.
        tag: The user-defined tag to lightly version the docker image.
        imageID: a SHA hash of the image contents.
        include_packages: Whether or not to record the current python
            packages when logging this environment.
    """
    def __init__(self,
                 imagename: str,
                 tag: str,
                 imageID: str,
                 include_packages: bool = False):
        self.imagename = imagename
        self.tag = tag
        self.imageID = imageID
        self.include_packages = include_packages

    @property
    def filename(self) -> str:
        # need to replace '/' with something else to avoid creating extra
        # directories
        return (f'{self.imagename.replace("/", "_")}'
                f'_{self.imageID.replace(":", "")}')

    @property
    def contents(self) -> str:
        contents_dict = {
            'CodeEnv type': 'Docker',
            'image name': self.imagename,
            'tag': self.tag,
            'image ID': self.imageID
            }

        if self.include_packages:
            contents_dict['packages'] = self.packagelist

        return json.dumps(contents_dict)

    @property
    def packagelist(self) -> list[tuple[str, str]]:
        """The environment of python packages."""
        return [(p.project_name, p.version)
                for p in pkg_resources.working_set]


class Process:
    """A representation of a process that affects a CloudVolume.

    Attributes:
        description: A user-defined description of what the process
            accomplishes.
        parameters: The parameters used by the process.
        *code_envs: The code environments used for this process.
    """
    def __init__(self,
                 description: str,
                 parameters: Union[dict, SimpleNamespace, ConfigParser],
                 *code_envs: list[CodeEnv]):
        self.description = description
        self.parameters = parameters
        self.code_envs = code_envs

    def log(self) -> tuple[dict[str, str], list[str]]:
        """Packaging the attributes for logging.

        Returns:
            A dictionary containing the task description, a parameter
            dictionary, and information about the code environment files.
            Also returns a list of strings containing the contents of each
            code environment file.
        """
        params = self.logparams()

        code_envfiles, code_envfilecontents = list(), list()
        for code_env in self.code_envs:
            new_envfile, new_envfilecontents = code_env.log()
            code_envfiles.append(new_envfile)
            code_envfilecontents.append(new_envfilecontents)

        return ({'task': self.description,
                 'parameters': params,
                 'code_envfiles': code_envfiles},
                code_envfilecontents)

    def logparams(self) -> dict:
        """Packaging the parameters for logging.

        Converts different ways of representing parameters into a flat
        dictionary.

        Returns:
            A dictionary containing the parameters.
        """
        if isinstance(self.parameters, dict):
            return self.parameters
        elif type(self.parameters) in [SimpleNamespace, ConfigParser]:
            return vars(self.parameters)
        else:
            raise NotImplementedError('parameter object for process'
                                      f'"{self.description}" has type '
                                      f'{type(self.parameters)},'
                                      ' which is not currently supported')


def logprocess(cloudvolume: cv.CloudVolume,
               process: Process,
               duplicate: bool = False
               ) -> None:
    """Logs a processing step to the provenance file.

    Args:
        cloudvolume: A CloudVolume.
        process: A Process to log.
        duplicate: Whether to log the a process even if it has already been
            logged.
    """
    provenance_dict, envfilecontents = process.log()
    envfilenames = provenance_dict['code_envfiles']

    if duplicate or process_absent(cloudvolume, process):
        logcodefiles(cloudvolume, envfilenames, envfilecontents)
        cloudvolume.provenance.processing.append(provenance_dict)

    else:
        raise AssertionError('duplicate set to False,'
                             f' and process {process.description}'
                             'has already been logged')

    cloudvolume.commit_provenance()


def process_absent(cloudvolume: cv.CloudVolume, process: Process) -> bool:
    """Checks whether a process is contained in a provenance file.

    Parses the provenance file for a given CloudVolume and determines
    whether a process has already been logged. Returns True if the process
    is absent.

    Args:
        cloudvolume: A CloudVolume.
        process: A Process.

    Returns:
        A bool describing whether or not the process is absent from
        the CloudVolume's provenance log.
    """
    logged = cloudvolume.provenance.processing

    def sameproc(loggedprocess: Process):
        return (loggedprocess['task'] == process.description
                and loggedprocess['parameters'] == process.parameters)

    candidates = list(filter(sameproc, logged))

    if len(candidates) == 0:
        return True


def logcodefiles(cloudvolume: cv.CloudVolume,
                 filenames: list[str],
                 filecontents: list[str]
                 ) -> None:
    """Logs the code environment files that haven't been logged already.

    Args:
        cloudvolume: A CloudVolume.
        filenames: A list of filenames to log.
        filecontents: The contents of each file to log.
    """
    absentfilenames, absentfilecontents = list(), list()
    for filename, filecontent in zip(filenames, filecontents):
        if codefile_absent(cloudvolume, filename):
            absentfilenames.append(filename)
            absentfilecontents.append(filecontent)

    logjsonfiles(cloudvolume, absentfilenames, absentfilecontents)


def codefile_absent(cloudvolume: cv.CloudVolume, filename: str) -> bool:
    """Checks whether a code environment has been logged in a CloudVolume.

    Parses the provenance file for a given CloudVolume and determines
    whether a code environment file has already been logged. Returns True if
    the process is absent.

    Args:
        cloudvolume: A CloudVolume.
        filename: A code environment filename.

    Returns:
        A bool describing whether or not the code environment file is absent
        from the CloudVolume's provenance log.
    """
    processes = cloudvolume.provenance.processing
    codefilenames = []
    for process in processes:
        if 'code_envfiles' in process:
            codefilenames.extend(process['code_envfiles'])

    return filename not in codefilenames


def logjsonfiles(cloudvolume: cv.CloudVolume,
                 filenames: list[str],
                 filecontents: list[str]
                 ) -> None:
    """Stores extra JSON files alongside a provenance file.

    Args:
        cloudvolume: A CloudVolume.
        filenames: A list of filenames to log.
        filecontents: The contents of each file to log.
    """
    for filename, filecontent in zip(filenames, filecontents):
        utils.sendjsonfile(cloudvolume, filename, filecontent)
