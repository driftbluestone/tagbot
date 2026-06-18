# module currently in development
from utils import config

class Group:
    def __init__(self, perms: dict, TLG: bool = False):
        self.TLG = TLG
        for k, v in perms.items():
            try:
                setattr(self, k, Permission(**v))
            except TypeError:
                if self.TLG:
                    setattr(self, k, Extension(v))
                else:
                    setattr(self, k, Group(v))

class Permission:
    def __init__(self, display_name: str, toggleable: bool, default_enabled: bool, role_assignable: bool):
        self.display_name = display_name
        self.toggleable = toggleable
        self.default_enabled = default_enabled
        self.role_assignable = role_assignable

class Extension:
    def __init__(self, perms: dict):
        for k, v in perms.items():
            try:
                setattr(self, k, Permission(**v))
            except TypeError:
                setattr(self, k, Group(v))

def to_dict(obj):
    # If the item has a __dict__ attribute, process its internal properties
    if hasattr(obj, '__dict__'):
        return {key: to_dict(value) for key, value in obj.__dict__.items() if not key.startswith('_')}
    
    # If it is a dictionary, process its keys and values
    elif isinstance(obj, dict):
        return {key: to_dict(value) for key, value in obj.items()}
    
    # If it is a list, tuple, or set, process each element
    elif isinstance(obj, (list, tuple, set)):
        return [to_dict(item) for item in obj]
    
    # Return primitive types (strings, ints, floats, bools, None) as they are
    return obj

Permissions = Group(config.permissions_config, True)

