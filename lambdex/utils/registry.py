__all__ = ['FunctionRegistry']


class FunctionRegistry:
    """
    A registry with values being functions.
    """
    _empty = object()

    def __init__(self, name: str):
        self.name = name
        self.mapping = {}
        self.__default = self._empty

    def register(self, key, value=_empty):
        """
        If `value` provided, register it with key `key`.
        Otherwise return a decorator.
        """
        if value is not self._empty:
            if not callable(value):
                value = lambda: value
            self.mapping[key] = value
            return

        def _decorator(f):
            self.mapping[key] = f
            return f

        return _decorator

    def get(self, key, default=_empty):
        """
        Return corresponding value of key `key`.

        If not found and `default` provided, `default` is returned.
        Otherwise, if default value of `self` set, the value is returned.
        Otherwise, raise a KeyError.
        """
        value = self.mapping.get(key, self._empty)
        if value is not self._empty:
            return value
        if default is not self._empty:
            return default
        if self.__default is not self._empty:
            return self.__default
        raise KeyError(key)

    def set_default(self, value):
        """
        Set `value` as the default value of the registry.
        """
        self.__default = value
        return self