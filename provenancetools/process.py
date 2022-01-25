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

    def __init__(self, name: str, parameters: Union[dict, Namespace],
                 code_env: CodeEnvT):
        self.name = name
        self.parameters = parameters
        self.code_env = code_env

    def log(self) -> Tuple[Dict[str, str], List[str]]:
        '''Returns the data to log'''
        codefile, codefilecontents = self.codeenv.log()
        return ({'task': self.name,
                 'parameters': self.parameters,
                 'codefiles': [codefile]},
                [codefilecontents])


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
        contents['commithash'] = self.commithash
        contents['diff'] = self.diff

        return contents


def repo_name_from_url(repo_url):
    '''Extracts the bare repo-name from a URL'''
    return os.path.basename(repo_url).replace('.git', '')


def logprocess(self, cloudvolume: CloudVolume, process: Process,
               duplicate: bool = False) -> None:
    '''Adds a documented processing step to the provenance log'''

    provenance_dict, extrafiles = process.log()
    if process_absent(cloudvolume, process.name):
        cloudvolume.provenance.processing.append(provenance_dict)
        logextrafiles(cloudvolume, process.name, extrafiles)

    elif duplicate:
        cloudvolume.provenance.processing.append(provenance_dict)

    else:
        raise AssertionError('duplicate set to False,'
                             f' yet process {process.name} already logged')

    cloudvolume.commit_provenance()


def logextrafiles(cloudvolume: CloudVolume, processname: str,
                  extrafilecontents: List[str]) -> None:
    filenames = [f'{processname}{i}' for i in range(len(extrafilecontents))]
    for filename, extrafilecontent in zip(filenames, extrafilecontents):
        utils.sendfile(cloudvolume, filename, extrafilecontent)
