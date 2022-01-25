'''Basic utilities'''
from cloudfiles import CloudFiles


def sendfile(cloudvolume, filename, content):
    cf = CloudFiles(cloudvolume.cloudpath)
    cf.put(filename, content, content_type='raw')
