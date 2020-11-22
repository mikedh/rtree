"""
finder.py
------------

Locate `libspatialindex` shared library by any means necessary.
"""
import os
import ctypes
import platform
from ctypes.util import find_library

# the current working directory of this file
_cwd = os.path.abspath(os.path.expanduser(
    os.path.dirname(__file__)))

# generate a bunch of candidate locations where the
# libspatialindex shared library *might* be hanging out
_candidates = [
    os.environ.get('SPATIALINDEX_C_LIBRARY', None),
    _cwd,
    os.path.join(_cwd, 'lib'),
    '']


def load():
    """
    Load the `libspatialindex` shared library.

    Returns
    -----------
    rt : ctypes object
      Loaded shared library
    """
    if os.name == 'nt':
        # check the platform architecture
        if '64' in platform.architecture()[0]:
            arch = '64'
        else:
            arch = '32'
        lib_name = 'spatialindex_c-{}.dll'.format(arch)

        # get the current PATH
        oldenv = os.environ.get('PATH', '').strip().rstrip(';')
        # run through our list of candidate locations
        for path in _candidates:
            if not path or not os.path.exists(path):
                continue
            # temporarily add the path to the PATH environment variable
            # so Windows can find additional DLL dependencies.
            os.environ['PATH'] = ';'.join([path, oldenv])
            try:
                rt = ctypes.cdll.LoadLibrary(os.path.join(path, lib_name))
                if rt is not None:
                    return rt
            except (WindowsError, OSError):
                pass
            except BaseException as E:
                print('rtree.finder unexpected error: {}'.format(str(E)))
            finally:
                os.environ['PATH'] = oldenv
        raise OSError("could not find or load {}".format(lib_name))

    elif os.name == 'posix':
        # generate a bunch of candidate locations where the
        # libspatialindex_c.so *might* be hanging out
        _candidates.append(find_library('spatialindex_c'))

        # posix includes both mac and linux
        # use the extension for the specific platform
        if platform.system() == 'Darwin':
            # macos shared libraries are `.dylib`
            extension = 'dylib'
            # set the magic search path for referenced libraries here
            dyld = os.environ.get('DYLD_LIBRARY_PATH', '').strip().rstrip(':')
        else:
            # linux shared libraries are `.so`
            extension = 'so'
            dyld = None

        # get the starting working directory
        cwd = os.getcwd()
        for cand in _candidates:
            if cand is None:
                continue
            elif os.path.isdir(cand):
                # if our candidate is a directory use best guess
                path = cand
                target = os.path.join(
                    cand, "libspatialindex_c.{}".format(extension))
            elif os.path.isfile(cand):
                # if candidate is just a file use that
                path = os.path.split(cand)[0]
                target = cand
            else:
                continue

            try:
                # move to the location we're checking
                os.chdir(path)

                if dyld is not None:
                    # on mac add our candidate to the search path
                    os.environ['DYLD_LIBRARY_PATH'] = ':'.join([dyld, path])

                # try loading the target file candidate
                rt = ctypes.cdll.LoadLibrary(target)
                if rt is not None:
                    return rt
            except BaseException as E:
                print('rtree.finder unexpected error: {}'.format(str(E)))
            finally:
                os.chdir(cwd)

    raise OSError("Could not load libspatialindex_c library")
