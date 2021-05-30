class CtrlZTray:
    _self = None

    def __init__(self):
        if self is not None:
            raise TypeError('{} already initiated'.format(type(self).__name__))
        self.deleted_stuff = []

    @classmethod
    def get_instance(cls):
        if cls._self is None:
            raise TypeError('{} not initiated'.format(type(cls).__name__))
        return cls._self
