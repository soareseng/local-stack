import importlib.util
import sys
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[1]

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))


def load_service_module(service_name: str):
    module_name = f"{service_name.replace('-', '_')}_app"
    file_path = SERVICES_DIR / service_name / "app.py"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module
