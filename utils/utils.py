import inspect
from pathlib import Path
DIR = Path(inspect.stack()[1].filename).parent.resolve()
