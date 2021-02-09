import sys
from os.path import dirname, abspath

ROOT_DIR = dirname(dirname(__file__))


def get_importer_path():
    """
    Find the first frame that imports lambdex. Return its file path
    if any.
    """
    f = sys._getframe(1)
    filename = None
    while f is not None and f.f_code is not None:
        filename = abspath(f.f_code.co_filename)

        # If it's in importlib or in lambdex, continue
        if 'importlib' in filename or filename.startswith(ROOT_DIR):
            f = f.f_back
        else:
            break

    return filename


def get_site_paths():
    import site

    if hasattr(site, 'getsitepackages'):
        yield from site.getsitepackages()

    if hasattr(site, 'getusersitepackages'):
        yield site.getusersitepackages()
