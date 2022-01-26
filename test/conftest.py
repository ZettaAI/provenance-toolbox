'''
Testing setup and teardown functionality

Creates a dummy CloudVolume and tears it down if specified below
(by commenting/uncommenting... I know)
'''
import os
import glob
import pytest
import cloudvolume as cv


# Location of the dummy CloudVolume
DUMMY_CV_PATH = "./test/test_cv"


def make_testcloudvolume(path):
    'Makes a dummy CloudVolume'
    num_channels = 1
    layer_type = 'segmentation'
    data_type = 'uint32'
    encoding = 'raw'
    resolution = (4, 4, 40)
    voxel_offset = (0, 0, 0)
    volume_size = (1024, 1024, 512)
    chunk_size = (64, 64, 64)

    info = cv.CloudVolume.create_new_info(
               num_channels, layer_type, data_type,
               encoding, resolution, voxel_offset,
               volume_size, chunk_size=chunk_size)

    vol = cv.CloudVolume(f'file://{path}', mip=0, info=info)

    vol.commit_info()

    return vol

    
def removefiles(expr):
    'Removes all files specified by a glob expression'
    filenames = glob.glob(expr)
    for filename in filenames:
        os.remove(filename)


def teardown(path):
    'Tears down the creation of a dummy cloudvolume at a particular path'
    removefiles(os.path.join(path, "*"))
    os.rmdir(path)


@pytest.fixture
def testcloudvolume_with_td():
    'Fixture that creates dummy CV and tears it down afterwards'
    yield make_testcloudvolume(DUMMY_CV_PATH)
    teardown(DUMMY_CV_PATH)


@pytest.fixture
def testcloudvolume_no_td():
    'Fixture that creates dummy CV and leaves it up afterwards'
    yield make_testcloudvolume(DUMMY_CV_PATH)


# Uncomment to skip teardown of the dummy CloudVolume
# (useful to inspect the resulting files, etc.)
#@pytest.fixture
#def testcloudvolume(testcloudvolume_no_td):
#    return testcloudvolume_no_td


# Uncomment to include teardown of the dummy CloudVolume
@pytest.fixture
def testcloudvolume(testcloudvolume_with_td):
    return testcloudvolume_with_td
