import inspect
import utils.callable_module as CallableModule
from pathlib import Path

@CallableModule
def ext() -> str:
    for k in inspect.stack():
        stack = Path(k.filename).parts
        for i, item in enumerate(stack):
            if item == "extensions":
                return stack[i+1]
