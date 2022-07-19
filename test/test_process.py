import os
import json
from provenancetoolbox import process
from collections import namedtuple

import pytest
import git


RepoInfo = namedtuple('RepoInfo', ['name', 'url', 'currenthash'])

SYNAPTOR_DESC = 'Doing something with the Synaptor docker container'
SYNAPTOR_PARAMS = {}
SYNAPTOR_IMAGE = 'zettaai/synaptor'
SYNAPTOR_TAG = 'floatresolutions'
SYNAPTOR_ID = 'c64d9d42ac38'
SYNAPTOR_DESC2 = 'Doing something else with the Synaptor docker container'
SYNAPTOR_ID2 = 'c64d9d42ac3802983749023784'


@pytest.fixture
def thisrepoinfo():
    'Info extracted from this git repo when called using GitPython'
    repo = git.Repo('.')
    name = 'provenance-tools'
    url = 'https://github.com/ZettaAI/provenance-tools.git'
    currenthash = repo.commit().hexsha

    return RepoInfo(name, url, currenthash)


@pytest.fixture
def thisPythonGithubEnv():
    'Representing this code environment using the PythonGithubEnv class'
    return process.PythonGithubEnv('.')


@pytest.fixture
def thisProcess(thisPythonGithubEnv):
    'A dummy process that uses thisPythonGithubEnv as a test'
    description = 'Adding not so useful documentation'
    parameters = {}

    return process.Process(description, parameters, thisPythonGithubEnv)


@pytest.fixture
def thisProcessWParams(thisPythonGithubEnv):
    'A dummy process that has parameters in contrast to the last one'
    description = 'Adding not so useful documentation'
    parameters = {'a': 3, 'b': 4}

    return process.Process(description, parameters, thisPythonGithubEnv)


@pytest.fixture
def SynaptorDockerEnv():
    return process.DockerEnv(SYNAPTOR_IMAGE, SYNAPTOR_TAG,
                             SYNAPTOR_ID)


@pytest.fixture
def SynaptorDockerEnvWPackages():
    return process.DockerEnv(SYNAPTOR_IMAGE, SYNAPTOR_TAG,
                             SYNAPTOR_ID2, include_packages=True)


@pytest.fixture
def SynaptorDockerProcess(SynaptorDockerEnv):
    'A dummy process using a Synaptor docker image'
    return process.Process(SYNAPTOR_DESC, SYNAPTOR_PARAMS, SynaptorDockerEnv)


@pytest.fixture
def SynaptorDockerProcessWPackages(SynaptorDockerEnvWPackages):
    'A dummy process using a Synaptor docker image'
    return process.Process(SYNAPTOR_DESC2, SYNAPTOR_PARAMS,
                           SynaptorDockerEnvWPackages)


def test_PythonGithubEnv(thisrepoinfo, thisPythonGithubEnv):
    'Tests for the PythonGithubEnv class representation'
    assert thisPythonGithubEnv.repo_name == thisrepoinfo.name
    assert thisPythonGithubEnv.url == thisrepoinfo.url
    assert thisPythonGithubEnv.commithash == thisrepoinfo.currenthash
    assert thisPythonGithubEnv.filename == (f'{thisrepoinfo.name}'
                                            f'_{thisrepoinfo.currenthash}')


def basicProcessTests(testcloudvolume, testprocess):
    'Some basic tests for any kind of process'
    origprocessinglength = len(testcloudvolume.provenance.processing)

    process.logprocess(testcloudvolume, testprocess)

    # Does the provenance file exist after logging?
    testcvname = os.path.basename(testcloudvolume.cloudpath)
    assert os.path.exists(f"test/{testcvname}/provenance")

    # Does the provenance file include a new item?
    testprov = testcloudvolume.provenance
    newprocessinglength = len(testcloudvolume.provenance.processing)
    assert newprocessinglength == origprocessinglength + 1

    # Does the newest process represent the correct info?
    newestprocess = testprov.processing[-1]
    assert newestprocess['task'] == testprocess.description
    assert newestprocess['parameters'] == testprocess.parameters
    assert len(newestprocess["code_envfiles"]) == len(testprocess.code_envs)


def readNewestCodeEnvFile(testcloudvolume, i):
    'Reads the content of the newest code environment file at index i'
    testcvlocal = testcloudvolume.cloudpath.replace("file://", "")
    provenance = testcloudvolume.provenance
    codeenvfilelocal = provenance.processing[-1]["code_envfiles"][i]
    testfile = os.path.join(testcvlocal, codeenvfilelocal)

    with open(testfile) as f:
        return json.load(f)


def test_logPythonGithubEnv(testcloudvolume, thisProcess):
    'Tests for logging PythonGithubEnv processes'
    basicProcessTests(testcloudvolume, thisProcess)

    # Does the code environment file store the correct information?
    content = readNewestCodeEnvFile(testcloudvolume, 0)
    testCodeEnv = thisProcess.code_envs[0]

    assert content['CodeEnv type'] == 'PythonGithub'
    assert content['name'] == testCodeEnv.url
    assert content['commit hash'] == testCodeEnv.commithash
    assert content['diff'] == testCodeEnv.diff
    assert content['packages'] == list(map(list, testCodeEnv.packagelist))


def test_logDockerEnv(testcloudvolume, SynaptorDockerProcess):
    'Tests for logging DockerEnv processes'
    basicProcessTests(testcloudvolume, SynaptorDockerProcess)

    # Does the code environment file store the correct information?
    content = readNewestCodeEnvFile(testcloudvolume, 0)
    testCodeEnv = SynaptorDockerProcess.code_envs[0]
    print(testCodeEnv.imagename)

    assert content['CodeEnv type'] == 'Docker'
    assert content['image name'] == testCodeEnv.imagename
    assert content['tag'] == testCodeEnv.tag
    assert content['image ID'] == testCodeEnv.imageID


def test_logDockerEnvWPackages(testcloudvolume,
                               SynaptorDockerProcessWPackages):
    'Tests for logging DockerEnv processes with python packages'
    basicProcessTests(testcloudvolume, SynaptorDockerProcessWPackages)

    # Does the code environment file store the correct information?
    content = readNewestCodeEnvFile(testcloudvolume, 0)
    testCodeEnv = SynaptorDockerProcessWPackages.code_envs[0]
    print(testCodeEnv.imagename)

    assert content['CodeEnv type'] == 'Docker'
    assert content['image name'] == testCodeEnv.imagename
    assert content['tag'] == testCodeEnv.tag
    assert content['image ID'] == testCodeEnv.imageID
    assert content['packages'] == list(map(list, testCodeEnv.packagelist))


def cleanprocessing(cloudvolume):
    cloudvolume.provenance.processing = []
    cloudvolume.commit_provenance()

def test_process_absent(testcloudvolume, thisProcess, thisProcessWParams):
    'Tests for process.process_absent'
    # Clear out any old processing
    cleanprocessing(testcloudvolume)

    basicProcessTests(testcloudvolume, thisProcess)

    assert not process.process_absent(testcloudvolume, thisProcess)
    assert process.process_absent(testcloudvolume, thisProcessWParams)

    basicProcessTests(testcloudvolume, thisProcessWParams)

    assert not process.process_absent(testcloudvolume, thisProcessWParams)
