"""
Use this module as a decorator to make that module callable as that function.
"""
import sys

def callable_module(func: function):
    class callableModule:
        def __init__(self, decorated: function):
            self._decorated = decorated
            self.__name__ = func.__module__
            self.__doc__ = func.__doc__

        def __call__(self, *args, **kwargs):
            return self._decorated(*args, **kwargs)
        
    sys.modules[func.__module__] = callableModule(func)
    return func

@callable_module
def CallableModule(func: function):
    callable_module(func)
