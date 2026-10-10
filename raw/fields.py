"""
The required fields for a model to count as **valid**
"""

REQUIRED = [
    ("name", str),
    ("version", str),
    ("model", dict),
    ("behaviour", dict),
    ("safe", (dict, type(None)))
]

EXAMPLE = {
    "name": None,
    "version": None,
    "model": {
        "provider": None,
        "name": None
    },
    "behaviour": {
        "skills": None,
        "spec": None
    },
    "safe": None
}

SKILL = {
    "module": None,
    "function-name": None,
    "args": None,
    "return-content-to-model": None,
    "desc": None
}

ARG = {
    "type": None,
    "name": None
}