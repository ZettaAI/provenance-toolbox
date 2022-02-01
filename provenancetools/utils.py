'''
utils.py

Basic utility functions
'''
from __future__ import annotations

import json

import docker
from cloudfiles import CloudFiles
import cloudvolume as cv


def sendjsonfile(cloudvolume: cv.CloudVolume,
                 filename: str,
                 content: str
                 ) -> None:
    'Stores a json file using CloudFiles'
    cf = CloudFiles(cloudvolume.cloudpath)

    prettycontent = json.loads(content)
    prettycontent = json.dumps(prettycontent,
                               sort_keys=True,
                               indent=2,
                               separators=(',', ': '))
    cf.put(filename, prettycontent,
           cache_control='no-cache',
           content_type='application/json')


def dockerimageID(imagename: str, tag: str) -> str:
    '''
    A tool to fetch the full image ID from a docker image name and tag

    Requires the current user to have access to the docker daemon.
    '''
    key = f'{imagename}:{tag}'

    client = docker.from_env()

    images = client.images.list()

    imagelookup = dict()
    for image in images:
        for tag in image.tags:
            assert tag not in imagelookup, 'multiple images have the same tag?'
            imagelookup[tag] = image.id

    if key in imagelookup:
        return imagelookup[key]
    else:
        raise ValueError(f'{key} not found in the current docker image list')
