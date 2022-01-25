import os
import glob
import pytest
import cloudvolume as cv


PATH = "./test/test_cv"




def make_testcloudvolume(path):

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
    filenames = glob.glob(expr)
    for filename in filenames:
        os.remove(filename)


def teardown(path):
    removefiles(os.path.join(path, "*"))
    os.rmdir(path)


@pytest.fixture
def testcloudvolume_with_td():
    yield make_testcloudvolume(PATH)

    teardown(PATH)


@pytest.fixture
def testcloudvolume_no_td():
    yield make_testcloudvolume(PATH)


@pytest.fixture
def testcloudvolume(testcloudvolume_no_td):
    return testcloudvolume_no_td
