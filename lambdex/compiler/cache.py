__all__ = [
    'get',
    'set',
    'set_enabled',
    'is_enabled',
]

_cache = {}
__enabled__ = True


def get(declarer):
    """
    Return the cached code object corresponding to `declarer`.

    If cache not enabled or not hit, return `None`.
    """
    if not __enabled__:
        return
    return _cache.get(declarer.get_key(), None)


def set(declarer, value):
    """
    Store `value` into the cache with `declarer` as key.

    If the key exists in cache, raise an error.
    """
    if not __enabled__:
        return
    key = declarer.get_key()
    assert key not in _cache
    _cache[key] = value


def set_enabled(value: bool):
    """
    Enable or disable the cache.
    """
    global __enabled__
    __enabled__ = value


def is_enabled() -> bool:
    """
    Check whether the cache is enabled.
    """
    return __enabled__