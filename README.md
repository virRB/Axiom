# Axiom

## What is This?

**A local AI agent manager built around customizable models and programmable skills.**

**Axiom** makes it intuitive to create, compile, and chat with agents that have user-defined skill sets and tool-calling capabilities in just minutes!

### Do I Need Internet?

Axiom uses local language models to generate responses, so **generating responses does not require an internet connection** when the local model server and required models are already set up. Internet access may still be needed for installation, downloading models, or other online operations.

### Can My Own Programs Talk to Axiom?

**Yes!**

**Axiom** provides a `--ask` option in the *CLI*, that returns a *JSON* string via **stdout**
***Command Syntax***
```bash
axiom --ask <model-name> <prompt> 
```
***Example Usage in Code***
```python
import subprocess, json

model = "ExampleAgent"
prompt = input(">>>> ")

response = subprocess.run(
    ["axiom", "--ask", model, prompt],
    text=True
).stdout
response = json.loads(response)
try:
    print(f"AI: {response['content']}") # The Response
except KeyError:
    print(f"{response['status']}: {response['reason']}") # If the response failed
```

### What Other Commands are there?

To see a list of all the commands that can be run in the **Axiom** *CLI*, run:
```bash
axiom --help
```

## How do I Install Axiom?

1. Download the **release** of your choice
2. Extract the release *ZIP* file, and in the extracted folder, open terminal
3. In the opened terminal, run:
```bash
./install
```

This command will only work if you have `python` installed and `pip` installed with it, and if the device it is being run on is Windows 11

## What do I Need for Axiom to Work?

**Axiom** currently requires:
1. **LM Studio**
```bash
winget install -e --id ElementLabs.LMStudio
```
> This uses `winget`, which should be available on most Windows 11 devices and some windows 10 devices
2. [**Python 3.11+**](http://python.org/downloads/)
3. Windows 11

## How do I Create A Model?

You can either create a model using the *CLI* interface, using the
```bash
axiom --create
```
command, **or** you can write it yourself.

To write one yourself, you must follow these steps:
1. Write all the skills as python functions and keep them all in, for example, `skills.py`
2. Create a file named `.agent.json`
3. Inside `.agent.json`, write the *JSON* for the model.
4. Right click the folder containing `skills.py` and `.agent.json` and select `Compress To...` > `ZIP File`
5. Name the created *ZIP* file whatever you want, for example `agent.zip`
6. Select a name for the agent, for example "MyAgent"
7. Select a model that this agent will base on. to see a list of reccomended models, run:
```bash
axiom --lsgmod
```
Let us take `qwen2.5-1.5b-instruct` as an example.
8. In that same directory, open up terminal and run:
```bash
axiom --compile "MyAgent" "agent.zip"
```
9. Run:
```bash
axiom -ls
```
to see your created models, and if all went well, you should see "MyAgent" in the list.

### Example
`skills.py`:
```python
import os

def read_file(name: str, api) -> dict:
    CWD = api.cwd
    path = os.path.join(CWD, name)
    if not os.path.exists(path):
        return {"status": "failed", "reason": f"\"{path}\" does not exist"}
    with open(path, "r", encoding="utf-8") as f:
        return {"status": "complete", "content": f.read()}

def exists_file(name: str, api) -> dict:
    CWD = api.cwd
    path = os.path.join(CWD, name)
    return {"status": "complete", "exists": str(os.path.exists(path))}
```

`.agent.json`:
```json
{
    "name": "MyAgent",
    "version": "v1.0",
    "model": {
        "name": "qwen2.5-1.5b-instruct",
        "provider": "local"
    },
    "behaviour": {
        "skills": {
            "read-file": {
                "module": "skills.py",
                "function-name": "read_file",
                "args": [
                    {
                        "name": "name",
                        "type": "<string>"
                    }
                ],
                "return-content-to-model": true,
                "desc": "Use this tool to read a file"
            },
            "exists-file": {
                "module": "skills.py",
                "function-name": "exists_file",
                "args": [
                    {
                        "name": "name",
                        "type": "<string>"
                    }
                ],
                "return-content-to-model": true,
                "desc": "Use this tool to check if a file exists or not"
            }
        },
        "spec": [
            "Use tools only when needed",
            "Be nice, concise and polite"
        ]
    },
    "safe": [
        "exists-file"
    ]
}
```

## Can You Explain That in More Detail?

Of course! Let's break down the `.agent.json` file and understand how Axiom agents work.

### The Basics

Every Axiom agent has a `.agent.json` file that defines its identity, model, behaviour, and available skills. Axiom reads this file when loading the agent.

### 1. `name`

```json
"name": "MyAgent"
```

This is the name of your agent. It identifies the agent in its definition and is useful when you're managing multiple agents.

### 2. `version`

```json
"version": "v1.0"
```

This specifies the version of the agent definition. You can use it to keep track of changes as you develop your agent.

### 3. `model`

```json
"model": {
    "name": "qwen2.5-1.5b-instruct",
    "provider": "local"
}
```

This section defines the language model your agent uses.

- **`name`** specifies the model identifier. For local models, this should match a model available through your LM Studio setup.
- **`provider`** specifies where the model comes from. `"local"` tells Axiom to use its local model provider.

The model generates responses and decides when to call available skills. The skills themselves are Python functions that you provide.

### 4. `behaviour`

The `behaviour` object defines how your agent behaves. It contains two important sections: `skills` and `spec`.

#### `behaviour.skills`

This section defines the tools available to your agent. Each skill has a name and a configuration describing how Axiom should load and use it.

For example:

```json
"read-file": {
    "module": "skills.py",
    "function-name": "read_file",
    "args": [
        {
            "name": "name",
            "type": "<string>"
        }
    ],
    "return-content-to-model": true,
    "desc": "Use this tool to read a file"
}
```

Let's break it down.

- **`read-file`** is the skill's identifier in the agent definition. The model can use the skill's description to decide when it is appropriate.
- **`module`** specifies the Python file containing the skill. In this example, the function is in `skills.py`.
- **`function-name`** specifies the exact Python function Axiom should load from that module. Here, it loads `read_file`.
- **`args`** defines the arguments the model can supply when calling the skill. Each argument has a `name` and a `type`.
- **`return-content-to-model`** determines whether the skill's result is returned to the model so it can use the result in its next reasoning step.
- **`desc`** describes what the skill does. A clear description helps the model determine when to use it.

You can define multiple skills in this section. Each can perform a different task, allowing you to build agents with different capabilities.

**Important:** A skill is real Python code, not a sandboxed instruction. Only use skills from sources you trust.

#### `behaviour.spec`

```json
"spec": [
    "Use tools only when needed",
    "Be nice, concise and polite"
]
```

This is a list of behavioural instructions supplied to the model.

You can use it to guide the agent's tone, explain how it should approach tasks, and encourage appropriate use of its tools.

For example, you could instruct an agent to answer concisely, use a particular format, or consult a skill when relevant.

These instructions guide the model; they are not a guarantee that it will always follow them.

### 5. The `safe` field

```json
"safe": [
    "exists-file"
]
```

This field appears at the root of the example definition, outside `behaviour`.

It lists the `exists-file` skill. This lists skills that can run without axiom asking for user permission before using the tool.

### How Do Python Skills Work?

Skills are ordinary Python functions. For example:

```python
def exists_file(name: str, api) -> dict:
    CWD = api.cwd
    path = os.path.join(CWD, name)
    return {
        "status": "complete",
        "exists": str(os.path.exists(path))
    }
```

Here, `name` is an argument supplied to the function, while `api` gives the function access to Axiom's runtime API.

When Axiom loads a skill, it uses the configured module and function name to locate the Python function. The model can then request that skill through tool calling, supplying the arguments defined in the agent configuration.

The function executes and returns a result to Axiom. Depending on the skill's configuration, that result may be passed back to the model.

### What Is the `api` Argument?

You may have noticed that the example skill accepts an argument called `api`:

```python
def read_file(name: str, api) -> dict:
    CWD = api.cwd
```

**`api` is an object supplied by Axiom to give skills access to shared runtime information and functionality.**

For example, `api.cwd` provides the current working directory exposed by Axiom's API. This lets a skill access runtime context without having to calculate or hardcode it independently.

A skill doesn't necessarily need this argument. Simple skills can accept only the arguments they require:

```python
def greet(name: str) -> dict:
    return {
        "status": "complete",
        "content": f"Hello, {name}!"
    }
```

When a skill needs access to Axiom's API, it can declare an `api` parameter:

```python
def show_directory(api) -> dict:
    return {
        "status": "complete",
        "content": api.cwd
    }
```

Axiom's runtime can inspect a skill's function signature and supply the API object when the function declares an `api` parameter.

This gives you a simple way to extend the information and functionality available to your skills as Axiom develops.

### Putting It All Together

An Axiom agent combines three things:

1. **A language model** that generates responses and decides when to call tools.
2. **Behavioural instructions** that guide how the agent responds.
3. **Python skills** that let the agent perform specific operations.

By combining these components, you can create agents tailored to your own workflows without having to build a separate AI application for each one.

## Stuff You should see
[LICENSE](LICENSE)
