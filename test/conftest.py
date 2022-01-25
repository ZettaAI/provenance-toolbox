import os
import glob
import pytest
import cloudvolume as cv


def removefiles(expr):
    filenames = glob.glob(expr)
    for filename in filenames:
        os.remove(filename)


@pytest.fixture
def testcloudvolume():

    path = "./test/test_cv"
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

    yield vol

    removefiles(os.path.join(path, "*"))
    os.rmdir(path)
