import os
import glob


TEST_CV_PATH = 'test/test_cv'


def removefiles(expr):
    'Removes all files specified by an expression'
    filenames = glob.glob(expr)
    for filename in filenames:
        os.remove(filename)


def teardown():
    'Tears down the test_cv if it exists'
    if os.path.isdir(TEST_CV_PATH):
        removefiles(os.path.join(TEST_CV_PATH, '*'))
        os.rmdir(TEST_CV_PATH)


if __name__ == '__main__':
    teardown()
