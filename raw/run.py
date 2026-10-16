"""
The internal functions used to run and load models from data.\n
Handles checking if a model is valid at the **secondary** and **root** level of the *JSON*
"""

import os
from paths import MODELS
import json
from compiler import validate_model
import fields
import importlib.util
from collections.abc import Callable
from openai import AsyncOpenAI
import subprocess
import inspect
import tool_api
from stuff import _input

TYPES = {
    "<string>": {"type": "string"},
    "<int>": {"type": "integer"},
    "<bool>": {"type": "boolean"},
    "<struct>": {"type": "object"}
}
"""
The JSON typing schema to convery <type> into
OpenAI compatible JSON
"""

def load_model(name: str) -> dict:
    """
    Loads a model from a name\n
    Also checks if it is valid at the **root** level.\n
    Raises **FileNotFoundError** if the model does not exist *OR* if the model lacks a manifest\n
    Raises **NotADirectoryError** if the model path is not a directory \n
    Raises **ValueError** if invalid *JSON* is found\n
    Raises **TypeError** if invalid *JSON* value types are found\n
    Raises **RuntimeError** in case of a model that is invalid at the **root** level
    """
    path = os.path.join(MODELS, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} does not exist!")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"{path} is not a folder!")
    manifest = os.path.join(path, ".agent.json")
    if not os.path.exists(manifest):
        raise FileNotFoundError(f"{manifest} does not exist!")
    try:
        with open(manifest, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        raise ValueError("Invalid JSON found")
    if not isinstance(j, dict):
        raise TypeError("Invalid JSON data type")
    key, valid, types = validate_model(j)
    if not valid:
        if types is not None:
            raise RuntimeError(f"Expected '{types[1]}', received '{types[0]}' under field '{key}'")
        else:
            raise RuntimeError(f"Missing field '{key}'")
    return j

def compare_keys(a: dict, b: dict) -> bool:
    """
    Recursively compare the keys of two dictionaries while ignoring the values
    """
    if a.keys() != b.keys():
        return False
    for key in a:
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            if not compare_keys(a[key], b[key]):
                return False
        elif isinstance(a[key], dict) or isinstance(b[key], dict):
            return False
    return True

def validate_model_secondary(agent: dict) -> bool:
    """
    Validate a model on the **secondary** level of the *JSON*
    """
    if not compare_keys(fields.EXAMPLE, agent):
        return False
    skills = agent["behaviour"]["skills"]
    if skills:
        if not isinstance(skills, dict):
            return False
        for _, val in skills.items():
            if not compare_keys(val, fields.SKILL):
                return False
    spec = agent["behaviour"]["spec"]
    if not isinstance(spec, (list, type(None))):
        return False
    if isinstance(spec, list):
        for item in spec:
            if not isinstance(item, str):
                return False
    safe = agent["safe"]
    safe = [] if safe is None else safe
    if not isinstance(safe, list):
        return False
    for s in safe:
        if not isinstance(s, str):
            return False
    return True

def _tool(name: str, desc: str, props: dict, required: list[str]) -> dict:
    """
    Returns a valid tool dict for **OpenAI** to use from the given parameters.
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required
            }
        }
    }

def load_module(path: str):
    """
    Load a module from a given file path.\n
    Raises **ImportError** if the module is invalid or failed to load
    """
    spec = importlib.util.spec_from_file_location("axiom_skill", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from '{path}'")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def tool(t: dict, name: str, skillname: str) -> tuple[dict, Callable, bool]:
    """
    Takes a user provided tool struct from `.agent.json` and returns:
    - An **OpenAI** compatible tool format *(tool[0])*\n
    - The function to be called when the model requests the tool *(tool[1])*\n
    - And a boolean determining if the return value of the function should be passed back to the model
    for further iterations or not *(tool[2])*\n
    ---
    This function returns a tuple that looks something like:\n
    `tuple[OpenAI-skill, function, return-content-to-model]`\n
    ---
    Raises **TypeError** in case the given 'tool' contains data that does not match the expected format\n
    Raises **FileNotFoundError** in case the model does not exist\n
    Raises **NotADirectoryError** in case the model path is not a folder\n
    Raises **ModuleNotFoundError** in case it could not find the file or package requested by the user\n
    Raises **KeyError** in case of an invalid argument data type\n
    Raises **AttributeError** if the function requested by the user does not exist\n
    Raises **ImportError** if the module requested by the user failed to load
    """
    if not compare_keys(t, fields.SKILL):
        raise TypeError("Given 'skill' does not match expected format for 'skill'")
    desc = t["desc"]
    if not isinstance(desc, str):
        raise TypeError("Description is meant to be a 'string'!")
    path = os.path.join(MODELS, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{name} does not exist!")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"The stored data for {name} is not a folder!")
    module = t["module"]
    module = os.path.join(path, module)
    if not os.path.exists(module):
        raise ModuleNotFoundError(f"Given file or package \"{t['module']}\" does not exist!")
    args = t["args"]
    if not isinstance(args, (list, type(None))):
        raise TypeError(f"Expected type 'list' or 'None', received '{type(args).__name__}'")
    args = [] if args is None else args
    for arg in args:
        if not compare_keys(arg, fields.ARG):
            raise TypeError("Given 'argument' does not match expected format for 'argument'")
        _type = arg["type"]
        if _type not in TYPES:
            raise KeyError(f"'{_type}' is not a valid data type")
    return_content_to_model = t["return-content-to-model"]
    if not isinstance(return_content_to_model, bool):
        raise TypeError(f"Expected 'return-content-to-model' to be either 'true' or 'false'")
    func_name = t["function-name"]
    module = load_module(module)
    if not hasattr(module, func_name):
        raise AttributeError(f"function '{func_name}' not found in module")
    func = getattr(module, func_name)
    if not callable(func):
        raise TypeError(f"'{func_name}' is not callable")
    props = {}
    for arg in args:
        _type = arg["type"]
        _name = arg["name"]
        props[_name] = TYPES[_type]
    __tool = _tool(name=skillname, desc=desc, props=props, required=list(props.keys()))
    return (__tool, func, return_content_to_model)

def sys_instruction_from_spec(agent: dict) -> dict:
    """
    Creates a system instruction that can be added as the first entry into the model's memory\n
    Raises **TypeError** if spec is not 'list' or 'None'
    """
    spec = agent["behaviour"]["spec"]
    if not isinstance(spec, (list, type(None))):
        raise TypeError(f"Spec should be either 'list' or 'None'")
    spec = "\n".join([] if spec is None else spec)
    spec = "No system instructions given" if spec == "" else spec
    return {"role": "system", "content": spec}

class Model:
    """
    the class containing a created **Model**\n
    ---
    Raises **TypeError** on creation if an unsupported provider is given
    """
    def __init__(self: "Model", name: str, model: str, version: str, provider: str, tools: list, api: tool_api.API, stdout: bool=True) -> None:
        """
        the class containing a created **Model**\n
        ---
        Raises **TypeError** on creation if an unsupported provider is given
        """
        self.name = name
        self.tools = tools
        self.model = model
        self.version = version
        self.provider = provider
        self.client = None
        self.api = api
        self.memory = list()
        if self.provider == "local":
            self.load(stdout=stdout)
        else:
            raise TypeError(f"Unsupported provider '{self.provider}'")
        self.path = os.path.join(MODELS, name)
        if not os.path.exists(self.path):
            raise FileNotFoundError("Model path does not exist!")
        if not os.path.isdir(self.path):
            raise NotADirectoryError("Model path is not a directory!")
        self.mem_path = os.path.join(self.path, "memory.json")
        with open(self.mem_path, "w", encoding="utf-8") as f:
            pass
    def load(self: "Model", stdout: bool=True) -> None:
        """
        Load the model using the ***LM Studio*** *CLI* (`lms`)\n
        Also initiates *`self.client`*\n
        ---
        Raises **FileNotFoundError** if ***LM Studio*** could not be found
        """
        try:
            subprocess.run(["lms", "load", self.model], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL if not stdout else None)
            subprocess.run(["lms", "server", "start"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise FileNotFoundError("LM studio is not installed OR not added to PATH")
        self.client = AsyncOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    def save(self: Model, file: str|None=None) -> None:
        """
        Saves the memory to a given file. *(default `self.mem_path`)*\n
        ---
        Raises **FileNotFoundError** if the given file does not exist\n
        Raises **IsADirectoryError** in case the given file is a directory
        """
        file = self.mem_path if file is None else file
        if not os.path.exists(file):
            raise FileNotFoundError(f"{file} does not exist!")
        if os.path.isdir(file):
            raise IsADirectoryError(f"{file} is a folder!")
        with open(file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f)
    async def ask(self: Model, prompt: str, confirm: Callable=_input, save: bool=True, steps: int=5, safe: list|None=None) -> dict:
        """
        Ask a prompt to the model and return the struct representing its response.\n
        Also handles execution of tools.\n
        """
        safe = [] if safe is None else safe
        def b_c_from_a(a: str) -> tuple[Callable, bool]|None:
            """
            Get the last two items of a three item tuple when the first item is provided.\n
            If it could not find the tuple then it returns `None`
            """
            for tool in self.tools:
                if tool[0]["function"]["name"] == a:
                    return (tool[1], tool[2])
            else:
                return None
        struct_prompt = {
            "role": "user",
            "content": prompt
        }
        self.push(struct_prompt, save=save)
        for step in range(steps):
            response = await self.client.chat.completions.create(model=self.model, messages=self.memory, temperature=0.2, tools=[tool[0] for tool in self.tools])
            message = response.choices[0].message
            if not message.tool_calls:
                result = message.model_dump()
                self.push(result, save=save)
                result["steps"] = str(step)
                return result
            self.push(message.model_dump(), save=save)
            for call in message.tool_calls:
                name = call.function.name
                arguments = json.loads(call.function.arguments)
                result = b_c_from_a(name)
                if result is None:
                    return {"role": "assistant", "content": "Called invalid tool"}
                _return = False
                if name not in safe:
                    confirmed = confirm(name)
                    if not confirmed:
                        output = {"status": "failed", "reason": "User declined permission to use this tool"}
                        _return = True
                    else:
                        func, _return = result
                        try:
                            signature = inspect.signature(func)
                            if "api" in signature.parameters:
                                arguments["api"] = self.api
                            output = func(**arguments)
                        except Exception as e:
                            output = {"status": "failed", "reason": f"User defined tool failed:\n{str(e)}"}
                else:
                    func, _return = result
                    try:
                        signature = inspect.signature(func)
                        if "api" in signature.parameters:
                            arguments["api"] = self.api
                        output = func(**arguments)
                    except Exception as e:
                        output = {"status": "failed", "reason": f"User defined tool failed:\n{str(e)}"}
                if not _return:
                    output = {"status": "complete"}
                self.push({"role": "tool", "tool_call_id": call.id, "content": json.dumps(output)}, save=save)
        return {"status": "failed", "content": "Maximum steps used"}
    def push(self: Model, message: dict, save: bool=True) -> None:
        """
        Pushes a instruction or message into the model's memory\n
        `save: bool=True` decides if the message history should be stored to the disk or not.\n
        ---
        Errors it may raise are listed under the *docstring* for `self.save`
        """
        self.memory.append(message)
        if save:
            self.save()


def _data_to_model(
            spec: dict,
            tools: list[tuple[dict, Callable, bool]],
            name: str,
            provider: str,
            model: str,
            version: str,
            api: tool_api.API,
            stdout: bool=True
            ) -> Model:
    """
    Takes the translated data and returns a **`Model`**\n
    ---
    Raises **TypeError** if an unsupported data type is given\n
    Raises **FileNotFoundError** if ***LM Studio*** was not found
    """
    agent = Model(name=name, model=model, version=version, provider=provider, tools=tools, api=api, stdout=stdout)
    agent.push(spec)
    return agent

def data_to_model(agent: dict, api: tool_api.API, stdout: bool=True) -> Model:
    """
    Takes an *agent* struct and returns a **`Model`** class\n
    ---
    Raises **TypeError** if 'spec' is not 'list' or 'None'\n
    ***OR*** in case the given 'tool' contains data that does not match the expected format\n
    Raises **FileNotFoundError** in case the model does not exist\n
    Raises **NotADirectoryError** in case the model path is not a folder\n
    Raises **ModuleNotFoundError** in case it could not find the file or package requested by the user\n
    Raises **KeyError** in case of an invalid argument data type\n
    Raises **AttributeError** if the function requested by the user does not exist\n
    Raises **ImportError** if the module requested by the user failed to load\n
    """
    spec = sys_instruction_from_spec(agent)
    name, version = agent["name"], agent["version"]
    model = agent["model"]
    provider = model["provider"]
    model = model["name"]
    behaviour = agent["behaviour"]
    skills = behaviour["skills"]
    _skills = []
    for n, data in skills.items():
        skill = tool(data, name, n)
        _skills.append(skill)
    return _data_to_model(
        spec=spec,
        tools=_skills,
        name=name,
        provider=provider,
        model=model,
        version=version,
        api=api,
        stdout=stdout
    )

def model_class_from_model_name(name: str, api: tool_api.API, stdout: bool=True) -> Model:
    """
    ---
    Raises **TypeError** if 'spec' is not 'list' or 'None'\n
    ***OR*** in case the given 'tool' contains data that does not match the expected format\n
    Raises **FileNotFoundError** in case the model does not exist\n
    **OR** in case ***LM Studio*** was not found\n
    Raises **NotADirectoryError** in case the model path is not a folder\n
    Raises **ModuleNotFoundError** in case it could not find the file or package requested by the user\n
    Raises **KeyError** in case of an invalid argument data type\n
    Raises **AttributeError** if the function requested by the user does not exist\n
    Raises **ImportError** if the module requested by the user failed to load\n
    """
    path = os.path.join(MODELS, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{name} does not exist!")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"{name} is not a directory!")
    agent = load_model(name)
    return data_to_model(agent, api=api, stdout=stdout)