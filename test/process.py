import os
from provenancetools import process
from collections import namedtuple

import pytest
import git

import cloudvolume as cv


RepoInfo = namedtuple("RepoInfo", ["name", "currenthash"])


@pytest.fixture
def thisrepoinfo():
    repo = git.Repo('.')
    name = 'provenance-tools'
    currenthash = repo.commit().hexsha

    return RepoInfo(name, currenthash)


@pytest.fixture
def thisPythonGithubEnv():
    return process.PythonGithubEnv('.')


@pytest.fixture
def thisProcess(thisPythonGithubEnv):
    name = 'Adding not so useful documentation'
    parameters = {}
    
    return process.Process(name, parameters, thisPythonGithubEnv)


def test_PythonGithubEnv(thisrepoinfo, thisPythonGithubEnv):
    assert thisPythonGithubEnv.repo_name == thisrepoinfo.name
    assert thisPythonGithubEnv.commithash == thisrepoinfo.currenthash
    assert thisPythonGithubEnv.filename == (f'{thisrepoinfo.name}'
                                            f'_{thisrepoinfo.currenthash}')


def test_logPythonGithubEnv(testcloudvolume, thisProcess):
    process.logprocess(testcloudvolume, thisProcess, duplicate=True)
    
    test_cv_name = os.path.basename(testcloudvolume.cloudpath)
    assert os.path.exists(f"test/{test_cv_name}/provenance")
