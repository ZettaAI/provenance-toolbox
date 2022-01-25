import os
import json
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
    processinglength = len(testcloudvolume.provenance.processing)
    process.logprocess(testcloudvolume, thisProcess, duplicate=True)

    testcvname = os.path.basename(testcloudvolume.cloudpath)
    assert os.path.exists(f"test/{testcvname}/provenance")

    testprov = testcloudvolume.provenance
    assert len(testprov.processing) == processinglength + 1
    assert testprov.processing[-1]['task'] == thisProcess.description
    assert testprov.processing[-1]['parameters'] == thisProcess.parameters
    assert len(testprov.processing[-1]["code_envfiles"]) == len(thisProcess.code_envs)

    testcvlocal = testcloudvolume.cloudpath.replace("file://", "")
    codeenvfilelocal = testprov.processing[-1]["code_envfiles"][0]
    testfile = os.path.join(testcvlocal, codeenvfilelocal)
    thisCodeEnv = thisProcess.code_envs[0]

    with open(testfile) as f:
        content = json.load(f)
    assert content['CodeEnvType'] == 'PythonGithub'
    assert content['name'] == 'provenance-tools'
    assert content['commithash'] == thisCodeEnv.commithash
    assert content['diff'] == thisCodeEnv.diff
