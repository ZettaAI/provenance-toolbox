import cloudvolume as cv


def main():

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

    vol = cv.CloudVolume('file://./test_cv', mip=0, info=info)

    vol.commit_info()


if __name__ == '__main__':
    main()
