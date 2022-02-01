import os
import json

import pytest
import docker

from provenancetools import utils


def test_sendjsonfile(testcloudvolume):
    'Simple test for utils.sendjsonfile'
    filename = 'test.json'
    contentdict = {'a': 3, 'b': 5, 'c': 'elephant'}
    content = json.dumps(contentdict)

    utils.sendjsonfile(testcloudvolume, filename, content)

    localcv = testcloudvolume.cloudpath.replace('file://', '')
    localfilename = os.path.join(localcv, filename)

    with open(localfilename) as f:
        recovered = json.load(f)

    assert recovered == contentdict
