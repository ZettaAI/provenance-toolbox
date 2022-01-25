'''Basic utilities'''
import json

from cloudfiles import CloudFiles


def sendfile(cloudvolume, filename, content):
    cf = CloudFiles(cloudvolume.cloudpath)
    cf.put(filename, content, content_type='raw')


def sendjsonfile(cloudvolume, filename, content):
    cf = CloudFiles(cloudvolume.cloudpath)

    prettycontent = json.loads(content)
    prettycontent = json.dumps(prettycontent,
                               sort_keys=True,
                               indent=2,
                               separators=(',', ': '))
    cf.put(filename, prettycontent,
           cache_control='no-cache',
           content_type='application/json')
