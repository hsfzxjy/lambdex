from ..definitions import State


class BaseAction:

    __slots__ = ['dont_consume', 'dont_store', 'dont_yield_buffer']

    @classmethod
    def is_class_of(cls, action):
        return action.__class__ is cls

    @classmethod
    def from_(cls, value) -> 'BaseAction':
        if value is None:
            return Default()

        assert isinstance(value, BaseAction)
        return value

    def __init__(self, *, dont_consume: bool = False, dont_store: bool = False, dont_yield_buffer: bool = False):
        self.dont_consume = dont_consume
        self.dont_store = dont_store
        self.dont_yield_buffer = dont_yield_buffer

    @property
    def no_special(self):
        return not (self.dont_consume or self.dont_store)

    def __repr__(self):
        attrs = ('{}={}'.format(name, getattr(self, name)) for name in self.__slots__)
        return '<{}: {}>'.format(
            self.__class__.__name__,
            ', '.join(attrs),
        )


class Default(BaseAction):
    pass


class StartBuffer(BaseAction):
    pass


class StopBuffer(BaseAction):
    pass


class Backtrace(BaseAction):

    __slots__ = BaseAction.__slots__ + ['new_state']

    def state(self, new_state: State) -> 'Backtrace':
        self.new_state = new_state
        return self


# default = BaseAction()
# dont_store = BaseAction()
# start_buffer = BaseAction()
# stop_buffer = BaseAction()
# dont_consume = BaseAction()
# stop_buffer_and_dont_consume = BaseAction()
# stop_buffer_and_dont_store = BaseAction()