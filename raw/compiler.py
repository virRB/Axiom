"""
The internal functions used to compile models from a *ZIP* file into data.\n
Handles checking if a model is valid at the **root** level of the *JSON*
"""

import os
import json
import zipfile
import fields
from paths import MODELS

def extract_model(file: str, name: str) -> str:
    """
    Extract a model *ZIP* into the models directory.\n
    Raises **FileExistsError** if the model already exists\n
    Raises **RuntimeError** in case extracting the *ZIP* file failed
    """
    temp = os.path.join(MODELS, name)
    if os.path.exists(temp):
        raise FileExistsError(f'Model "{name}" already exists!')
    os.makedirs(temp, exist_ok=True)
    try:
        with zipfile.ZipFile(file) as z:
            for member in z.infolist():
                parts = member.filename.split("/", 1)
                if len(parts) == 1:
                    continue
                member.filename = parts[1]
                if member.filename:
                    z.extract(member, temp)
    except Exception as e:
        if os.path.exists(temp):
            import shutil
            shutil.rmtree(temp)
        raise RuntimeError("Could not extract ZIP file") from e
    return temp

def load_model_json(model_dir: str) -> dict:
    """
    Load the `.agent.json` file from a model directory.\n
    Raises **ValueError** in case of invalid *JSON*\n
    Raises **TypeError** in case of invalid *JSON* object\n
    Raises **FileNotFoundError** in case of the absence of `.agent.json`\n
    """
    path = os.path.join(model_dir, ".agent.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f'"{path}" was not found')
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f'Invalid JSON in "{path}"') from e
    if not isinstance(data, dict):
        raise TypeError(f"Expected 'dict', found '{type(data).__name__}'")
    return data


def validate_model(agent: dict) -> tuple[str|None, bool, tuple[str, str]|None]:
    """
    Validate a model against the required fields.\n
    Returns **`tuple[key|None, valid, tuple[type, expected]|None]`**
    """
    for key, val in fields.REQUIRED:
        if key not in agent:
            return key, False, None
        if not isinstance(agent[key], val):
            if isinstance(val, tuple):
                name = f"{' or '.join(item.__name__ for item in val)}"
            else:
                name = val.__name__
            return (key, False, (type(agent[key]).__name__, name))
    return (None, True, None)


def compile_model(name: str, file: str) -> str:
    """
    Compile and validate a model *ZIP*.\n
    Raises **FileNotFoundError** in case the file being compiled does not exist\n
    Raises **IsADirectoryError** in case of the given file being a folder\n
    Raises **ValueError** in case of a missing key\n
    Raises **TypeError** in case of invalid value type
    """
    if not os.path.exists(file):
        raise FileNotFoundError(f'"{file}" does not exist')
    if os.path.isdir(file):
        raise IsADirectoryError(f'"{file}" is a folder, not a file')
    model_dir = extract_model(file, name)
    try:
        agent = load_model_json(model_dir)
    except Exception:
        import shutil
        shutil.rmtree(model_dir, ignore_errors=True)
        raise
    key, valid, types = validate_model(agent)
    if not valid:
        import shutil
        shutil.rmtree(model_dir, ignore_errors=True)
        if types is None:
            raise ValueError(f"Missing field '{key}'")
        raise TypeError(f"Expected type '{types[1]}', received '{types[0]}' in field '{key}'")
    return model_dir