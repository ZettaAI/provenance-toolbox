from provenancetools import process
import pytest
import git


def test_PythonGithubEnv():
    repo = git.Repo('.')

    env = process.PythonGithubEnv('.')

    assert env.repo_name == 'provenance-tools'
    assert env.commithash == '4b829ee941283ca2e8a45e7d63233144f3e225d1'
    assert env.filename == ('provenance-tools'
                            '_4b829ee941283ca2e8a45e7d63233144f3e225d1')
