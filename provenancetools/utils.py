'''Basic utilities'''
from cloudfiles import CloudFiles


def sendfile(basedir, filename, content):
    cf = CloudFiles(basedir)
    cf.put(filename, content, content_type='raw')
