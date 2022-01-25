from provenancetools import process
from collections import namedtuple
import pytest
import git


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


def test_PythonGithubEnv(thisrepoinfo, thisPythonGithubEnv):
    assert thisPythonGithubEnv.repo_name == thisrepoinfo.name
    assert thisPythonGithubEnv.commithash == thisrepoinfo.currenthash
    assert thisPythonGithubEnv.filename == (f'{thisrepoinfo.name}'
                                            f'_{thisrepoinfo.currenthash}')


def test_logPythonGithubEnv():
    pass
