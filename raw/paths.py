"""
Contains the frequently used paths\n
- **HERE**\n
- **MODELS**\n
*CWD* is not provided as it may differ from file to file
"""
import os
import sys
if getattr(sys, "frozen", False):
    HERE = os.path.dirname(os.path.abspath(sys.executable))
else:
    HERE = os.path.dirname(os.path.abspath(__file__))
APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
AXIOM = os.path.join(APPDATA, "AXIOM-BY-VIR-LOCALAPPDATA")
MODELS = os.path.join(AXIOM, "models")
TEMP = os.path.join(AXIOM, "temp")
os.makedirs(MODELS, exist_ok=True)
os.makedirs(TEMP, exist_ok=True)