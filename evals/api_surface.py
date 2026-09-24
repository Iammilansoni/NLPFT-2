"""
Benchmark API surface -- re-exported from the backend package.

The catalogue lives in Backend/app/demo_catalogue.py so the demo seed that runs
inside the backend image and this benchmark read the SAME twenty templates: the
numbers in the README are measured on exactly what a reviewer clicks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Backend"))

from app.demo_catalogue import API_TEMPLATES, TEMPLATES_BY_NAME, cluster_of  # noqa: E402,F401
