import importlib
import traceback
import sys
from pathlib import Path

# ensure backend folder is on sys.path so top-level 'app' package is importable
HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

try:
    importlib.import_module('app.main')
    print('Imported app.main successfully')
except Exception:
    traceback.print_exc()
