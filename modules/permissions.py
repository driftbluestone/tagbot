from dataclasses import dataclass

@dataclass
class Permission:
    display_name: str
    discord_equivalent: str = None
    toggleable: bool = True
    default_enabled: bool = False
    role_assignable: bool = True
