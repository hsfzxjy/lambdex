__all__ = [
    'get',
    'set',
    'set_enabled',
    'is_enabled',
]

_cache = {}
__enabled__ = True


def get(declarer):
    if not __enabled__:
        return
    return _cache.get(declarer.get_key(), None)


def set(declarer, value):
    if not __enabled__:
        return
    key = declarer.get_key()
    assert key not in _cache
    _cache[key] = value


def set_enabled(value: bool):
    global __enabled__
    __enabled__ = value


def is_enabled():
    return __enabled__