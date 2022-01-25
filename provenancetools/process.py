'''
'''
import os
import json
from typing import TypeVar, Union, List, Tuple, Dict

import pkg_resources
import git

from . import utils


CloudVolume = TypeVar('CloudVolume')
Namespace = TypeVar('Namespace')
CodeEnvT = TypeVar('CodeEnv')


class Process:
    '''A representation of a process that affects a CloudVolume'''

    def __init__(self, description: str, parameters: Union[dict, Namespace],
                 *code_envs: List[CodeEnvT]):
        self.description = description
        self.parameters = parameters
        self.code_envs = code_envs

    def log(self) -> Tuple[Dict[str, str], List[str]]:
        '''Returns the data to log'''
        code_envfiles, code_envfilecontents = list(), list()
        for code_env in self.code_envs:
            new_envfile, new_envfilecontents = code_env.log()
            code_envfiles.append(new_envfile)
            code_envfilecontents.append(new_envfilecontents)

        return ({'task': self.description,
                 'parameters': self.parameters,
                 'code_envfiles': code_envfiles},
                code_envfilecontents)


class CodeEnv:
    '''A representation of a code environment'''
    def __init__(self, codeptr: List[str]):
        self.codeptr = codeptr

    def log(self) -> Tuple[str, str]:
        return self.filename, self.contents

    @property
    def filename(self):
        raise NotImplementedError


class PythonGithubEnv(CodeEnv):
    def __init__(self, codeptr: str):
        self.codeptr = codeptr
        self.repo = git.Repo(codeptr)

    @property
    def filename(self):
        return f'{self.repo_name}_{self.commithash}'

    @property
    def repo_name(self):
        cfg = self.repo.config_reader()
        url = cfg.get('remote "origin"', 'url')

        return repo_name_from_url(url)

    @property
    def commithash(self):
        return self.repo.commit().hexsha

    @property
    def diff(self):
        return self.repo.git.diff()

    @property
    def packagelist(self):
        return [(p.project_name, p.version)
                for p in pkg_resources.working_set]

    @property
    def contents(self):
        contents = dict()

        contents['name'] = self.repo_name
        contents['CodeEnvType'] = 'PythonGithub'
        contents['commithash'] = self.commithash
        contents['diff'] = self.diff
        contents['packages'] = self.packagelist

        return json.dumps(contents)


def repo_name_from_url(repo_url):
    '''Extracts the bare repo-name from a URL'''
    return os.path.basename(repo_url).replace('.git', '')


def logprocess(cloudvolume: CloudVolume, process: Process,
               duplicate: bool = False) -> None:
    '''Adds a processing step to the provenance log documentation'''
    provenance_dict, envfilecontents = process.log()
    envfilenames = provenance_dict["code_envfiles"]

    if duplicate or process_absent(cloudvolume, process.description):
        logcodefiles(cloudvolume, envfilenames, envfilecontents)
        cloudvolume.provenance.processing.append(provenance_dict)

    else:
        raise AssertionError('duplicate set to False,'
                             f' yet process {process.description} already logged')

    cloudvolume.commit_provenance()


def process_absent(cloudvolume, processname):
    'Checks whether a process has already been logged. Returns True if not'
    processes = cloudvolume.provenance.processing
    processnames = [process["task"] for process in processes
                    if "task" in process]

    return processname not in processnames


def logcodefiles(cloudvolume: CloudVolume, filenames: List[str],
                 filecontents: List[str]) -> None:
    '''Logs the code environment files that haven't been logged already'''
    absentfilenames, absentfilecontents = list(), list()
    for filename, filecontent in zip(filenames, filecontents):
        if codefile_absent(cloudvolume, filename):
            absentfilenames.append(filename)
            absentfilecontents.append(filecontent)

    print(f"LOGGING {len(absentfilenames)} FILES")
    logjsonfiles(cloudvolume, absentfilenames, absentfilecontents)


def codefile_absent(cloudvolume: CloudVolume, filename: str):
    '''
    Checks whether a code environment file has already been logged.
    Returns True if not
    '''
    processes = cloudvolume.provenance.processing
    codefilenames = []
    for process in processes:
        if "code_envfiles" in process:
            codefilenames.extend(process["code_envfiles"])

    return filename not in codefilenames


def logjsonfiles(cloudvolume: CloudVolume, filenames: List[str],
                 filecontents: List[str]) -> None:
    for filename, filecontent in zip(filenames, filecontents):
        utils.sendjsonfile(cloudvolume, filename, filecontent)
