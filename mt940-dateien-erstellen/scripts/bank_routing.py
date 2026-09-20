"""Routing only: no bank-neutral MT940 renderer or fallback."""
import importlib.util
from pathlib import Path
BANKS={"dortmunder-volksbank-pdf-2025-v3":"dortmunder-volksbank"}

def model(data):
    name=BANKS.get(data.get("profile_id"))
    if not name:
        raise ValueError("No matching bank-specific model/reference file. Legacy and universal profiles are blocked.")
    path=Path(__file__).resolve().parent.parent/"banks"/name/"encode.py"
    spec=importlib.util.spec_from_file_location("bank_"+name.replace("-","_"),path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
