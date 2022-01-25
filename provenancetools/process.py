'''
'''
import os
from typing import TypeVar, Union, List, Tuple, Dict

import git

from . import utils


CloudVolume = TypeVar('CloudVolume')
Namespace = TypeVar('Namespace')
CodeEnvT = TypeVar('CodeEnv')


class Process:
    '''A representation of a process that affects a CloudVolume'''

    def __init__(self, description: str, parameters: Union[dict, Namespace],
                 code_env: CodeEnvT):
        self.description = description
        self.parameters = parameters
        self.code_env = code_env

    def log(self) -> Tuple[Dict[str, str], List[str]]:
        '''Returns the data to log'''
        code_envfile, code_envfilecontents = self.code_env.log()
        return ({'task': self.description,
                 'parameters': self.parameters,
                 'code_envfiles': [code_envfile]},
                [code_envfilecontents])


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
    def contents(self):
        contents = dict()

        contents['CodeEnvType'] = 'PythonGithub'
        contents['name'] = self.repo_name
        contents['commithash'] = self.commithash
        contents['diff'] = self.diff

        return bytes(str(contents), 'utf-8')


def repo_name_from_url(repo_url):
    '''Extracts the bare repo-name from a URL'''
    return os.path.basename(repo_url).replace('.git', '')


def logprocess(cloudvolume: CloudVolume, process: Process,
               duplicate: bool = False) -> None:
    '''Adds a documented processing step to the provenance log'''

    provenance_dict, code_envfilecontents = process.log()
    if process_absent(cloudvolume, process.description):
        cloudvolume.provenance.processing.append(provenance_dict)
        logextrafiles(cloudvolume, provenance_dict["code_envfiles"],
                      code_envfilecontents)

    elif duplicate:
        cloudvolume.provenance.processing.append(provenance_dict)

    else:
        raise AssertionError('duplicate set to False,'
                             f' yet process {process.description} already logged')

    cloudvolume.commit_provenance()


def process_absent(cloudvolume, processname):
    'Checks whether a process has already been logged. Returns True if not'
    processes = cloudvolume.provenance.processing
    for process in processes:
        if "task" in process and process["task"] == processname:
            return False

    return True


def logextrafiles(cloudvolume: CloudVolume, filenames: List[str],
                  filecontents: List[str]) -> None:
    for filename, filecontent in zip(filenames, filecontents):
        utils.sendfile(cloudvolume, filename, filecontent)
