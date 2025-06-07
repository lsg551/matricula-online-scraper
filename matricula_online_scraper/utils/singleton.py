"""This module provides a Singleton meta class for creating singleton classes."""


class Singleton(type):
    """Singleton meta class.

    Used as a metaclass, this class provides a way to ensure
    that only one instance of a class is created.

    Example:
    >>> class MySingleton(metaclass=Singleton):
    ...     pass
    >>> instance1 = MySingleton()
    >>> instance2 = MySingleton()
    >>> instance1 is instance2
    True
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):  # noqa: D102
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
