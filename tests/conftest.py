# /srv/predictatrade-ml/tests/conftest.py

import os
import sys

# Resolve project root (one directory up from /tests)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
