__all__ = ['FunctionRegistry']


class FunctionRegistry:

    _empty = object()

    def __init__(self, name: str):
        self.name = name
        self.mapping = {}
        self.__default = self._empty

    def register(self, key, value=_empty):

        if value is not self._empty:
            if not callable(value):
                value = lambda: value
            self.mapping[key] = value
            return

        def _decorator(f):
            self.mapping[key] = f

        return _decorator

    def get(self, key, default=_empty):
        value = self.mapping.get(key, self._empty)
        if value is not self._empty:
            return value
        if default is not self._empty:
            return default
        if self.__default is not self._empty:
            return self.__default
        raise KeyError(key)

    def set_default(self, value):
        self.__default = value
        return self