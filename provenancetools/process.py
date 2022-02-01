'''
process.py

Storage of a processing step (process) along with its code environments.
'''
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
    'A representation of a code environment - a virtual class'
    def __init__(self, codeptr: str):
        self.codeptr = codeptr

    def log(self) -> tuple[str, str]:
        '''
        Logging a code environment consists of specifying a
        "code environment file" that contains all of the required
        information to recover the environment. This method
        should collect that information from any subclass.
        '''
        return self.filename, self.contents

    @property
    def filename(self):
        raise NotImplementedError

    @property
    def contents(self):
        raise NotImplementedError


class PythonGithubEnv(CodeEnv):
    '''
    A representation of a code environment specified by a python
    environment and github repo.
    '''
    def __init__(self, codeptr: str):
        self.codeptr = codeptr
        self.repo = git.Repo(codeptr)

    @property
    def url(self) -> str:
        cfg = self.repo.config_reader()
        return cfg.get('remote "origin"', 'url')

    @property
    def repo_name(self) -> str:
        'The name of the github repo'
        return repo_name_from_url(self.url)

    @property
    def commithash(self) -> str:
        'The hash of the current commit of the github repo'
        return self.repo.commit().hexsha

    @property
    def diff(self) -> str:
        'The uncommitted code changes within the current environment'
        return self.repo.git.diff()

    @property
    def packagelist(self) -> list[tuple[str, str]]:
        'The environment of python packages'
        return [(p.project_name, p.version)
                for p in pkg_resources.working_set]

    @property
    def filename(self) -> str:
        'The code environment filename to store alongside the provenance file'
        return f'{self.repo_name}_{self.commithash}'

    @property
    def contents(self) -> str:
        'The contents of the code environment file'
        contents = dict()

        contents['name'] = self.url
        contents['CodeEnv type'] = 'PythonGithub'
        contents['commit hash'] = self.commithash
        contents['diff'] = self.diff
        contents['packages'] = self.packagelist

        return json.dumps(contents)


def repo_name_from_url(repo_url: str) -> str:
    'Extracts the bare repo-name from a URL'
    return os.path.basename(repo_url).replace('.git', '')


class DockerEnv(CodeEnv):
    '''
    A representation of a code environment specified by a
    docker image and tag.
    '''
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
        'The code environment filename to store alongside the provenance file'
        # need to replace '/' with something else to avoid creating extra
        # directories
        return (f'{self.imagename.replace("/", "_")}'
                f'_{self.imageID.replace(":", "")}')

    @property
    def contents(self) -> str:
        'The contents of the code environment file'
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
        'The environment of python packages'
        return [(p.project_name, p.version)
                for p in pkg_resources.working_set]


class Process:
    'A representation of a process that affects a CloudVolume'
    def __init__(self,
                 description: str,
                 parameters: Union[dict, SimpleNamespace, ConfigParser],
                 *code_envs: list[CodeEnv]):
        self.description = description
        self.parameters = parameters
        self.code_envs = code_envs

    def log(self) -> tuple[dict[str, str], list[str]]:
        'Returns the data to log'
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
    'Adds a processing step to the provenance log documentation'
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
    'Checks whether a process has already been logged. Returns True if not'
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
    '''Logs the code environment files that haven't been logged already'''
    absentfilenames, absentfilecontents = list(), list()
    for filename, filecontent in zip(filenames, filecontents):
        if codefile_absent(cloudvolume, filename):
            absentfilenames.append(filename)
            absentfilecontents.append(filecontent)

    logjsonfiles(cloudvolume, absentfilenames, absentfilecontents)


def codefile_absent(cloudvolume: cv.CloudVolume, filename: str) -> bool:
    '''
    Checks whether a code environment file has already been logged.
    Returns True if not
    '''
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
    'Stores extra JSON files alongside a provenance file'
    for filename, filecontent in zip(filenames, filecontents):
        utils.sendjsonfile(cloudvolume, filename, filecontent)
