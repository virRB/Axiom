"""
Used for the `--create` argument in the **CLI**\n
Used to create a model without writing *JSON* by hand
"""

from collections.abc import Callable
from typing import Any
from rich import print
from paths import TEMP, MODELS
from compiler import compile_model
import zipfile
import os
from stuff import error, done, _input
import json
import shutil
from run import TYPES

def zip_folder(folder_path: str, zip_path: str) -> None:
    """
    Zips a folder and all of its contents into the given *ZIP* path
    """
    parent = os.path.dirname(folder_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                archive_path = os.path.relpath(file_path, parent)
                archive.write(file_path, archive_path)

def ask_type(prompt: str, _type: Callable) -> Any:
    """
    Asks for a input of a specific type
    """
    def can_convert(v: str, t: Callable) -> bool:
        """
        Checks if a string can be converted to a specific type without raising an exception
        """
        try:
            t(v)
            return True
        except (TypeError, ValueError):
            return False
    while True:
        print(f"[bold bright_green]{prompt}[/bold bright_green][bold magenta] >>[/bold magenta]", end="")
        answer = input()
        if not can_convert(answer, _type):
            name = _type.__name__
            vowels = list("aeiou")
            if any(name.startswith(vowel) for vowel in vowels):
                preposition = "an"
            else:
                preposition = "a"
            print(f"[bold yellow]Expected {preposition} '{_type.__name__}'")
            continue
        return _type(answer)

def clear_temp() -> None:
    """
    Clears `TEMP`
    """
    for file in os.listdir(TEMP):
        path = os.path.join(TEMP, file)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def create_model(_json: dict, files: list[str], name: str) -> None:
    """
    Creates the model from the *JSON* and also bundles in the given files relative to the *CWD*
    """
    clear_temp()
    path_temp = os.path.join(TEMP, name)
    zip_temp = os.path.join(TEMP, f"{name}.zip")
    if os.path.exists(path_temp):
        error(f"{name} already exists!")
    os.makedirs(path_temp)
    agent_json = os.path.join(path_temp, ".agent.json")
    with open(agent_json, "w", encoding="utf-8") as f:
        f.write(json.dumps(_json, indent=4))
    for file in files:
        if not os.path.exists(file):
            error(f"'{os.path.basename(file)}' does not exist!")
        bundled = os.path.join(path_temp, os.path.basename(file))
        if os.path.exists(bundled):
            error(f"'{bundled}' has already been given!")
        shutil.copy(file, bundled)
    zip_folder(path_temp, zip_temp)
    compile_model(name, zip_temp)
    os.remove(zip_temp)
    shutil.rmtree(path_temp)
    done(f"Created '{name}'!")

def pure_bool(o: str) -> bool:
    if o.lower() not in ["true", "false"]:
        raise TypeError(f"'{o}' is not a bool!")
    return True if o.lower() == "true" else False

def pure_type(o: str) -> dict:
    if o.lower() not in TYPES.keys():
        raise TypeError(f"'{o}' is not a valid type!")
    return o.lower()

def ask_input_for_json(CWD: str) -> tuple[dict, list[str], str]:
    """
    Ask for user input and create the `.agent.json` contents from it
    """
    _json = dict()
    name = ask_type("Name", str)
    modeldir = os.path.join(MODELS, name)
    if os.path.exists(modeldir):
        error(f"{name} already exists!")
    version = ask_type("Version", str)
    model = ask_type("Model Name", str)
    skills = dict()
    files = []
    print("[bold yellow]Now creating skills\n"
        "Enter 'DONE' as the skill name if you have created all the skills\n"
        "If you want the skill name to be 'DONE' enter 'r#DONE' as the skill name[/bold yellow]")
    while True:
        skillname = ask_type("Skill Name", str)
        if skillname.lower() == "done":
            break
        elif skillname.lower() == "r#done":
            skillname = skillname.removeprefix("r#")
        if skillname in skills:
            error(f"{skillname} already exists!")
        filename = ask_type("Python Module", str)
        file = os.path.join(CWD, filename)
        if not os.path.exists(file):
            error(f"{file} was not found!")
        funcname = ask_type("Python Function Name", str)
        return_content = ask_type("Return Content to Model", pure_bool)
        args = list()
        print(f"[bold yellow]Now creating arguments for '{skillname}'\n"
            "Enter 'DONE' as the argument name if you have mentioned all the arguments needed\n"
            "If you want the argument to be named 'DONE', enter 'r#DONE' as the argument name\n"
            "the API does not need to be included, if the function contains an argument named 'api' it is automatically passed[bold yellow]")
        while True:
            argname = ask_type("Argument Name", str)
            if argname.lower() == "done":
                break
            elif argname.lower() == "r#done":
                argname = argname.removeprefix("r#")
            typename = ask_type(f"Argument Type:\n{'\n'.join(list(TYPES.keys()))}\n", pure_type)
            arg = {
                "name": argname,
                "type": typename
            }
            args.append(arg)
        desc = ask_type("Describe this Tool", str)
        if filename not in files:
            files.append(file)
        skills[skillname] = {
            "module": filename,
            "function-name": funcname,
            "args": args,
            "return-content-to-model": return_content,
            "desc": desc
        }
    spec = ask_type("System Instructions", str)
    behaviour = {
        "skills": skills,
        "spec": [spec]
    }
    _json = {
        "name": name,
        "version": version,
        "model": {
            "name": model,
            "provider": "local"
        },
        "behaviour": behaviour,
        "safe": None
    }
    show_json = _input(None, normal=True, prompt="Show the created JSON? [y/n]")
    if show_json:
        print(json.dumps(_json, indent=4))
    return (_json, files, name)

def magic_stuff(CWD: str) -> None:
    """
    A magician **never** reveals his secrets.\n
    *yeah.*\n
    Totally not because I'm tired of writing *docstrings*
    """
    stuff = ask_input_for_json(CWD)
    create_model(*stuff)