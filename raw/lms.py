"""
The ***LM Studio*** integration for **Axiom**
"""
import requests
import shutil
import subprocess
import time
from rich import print
import sys
from stuff import error, _input

MODELS = {
    "qwen2.5-1.5b-instruct": {
        "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    }
}

def check_lms() -> bool:
    """
    Checks if ***LM Studio*** is available via *CLI*
    """
    lms = shutil.which("lms")
    if lms is None:
        return False
    else:
        return True

def check_lms_server() -> bool:
    """
    Checks if ***LM Studio*** is available on `localhost:1234`
    """
    try:
        lms = requests.get("http://localhost:1234/v1/models", timeout=5)
        lms.raise_for_status()
        return True
    except (requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError):
        return False

def start_lms_server() -> None:
    """
    Run the `lms server start` command
    """
    subprocess.run(["lms", "server", "start"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

def confirm_lms() -> None:
    """
    Confirms that ***LM Studio*** is online on `localhost:1234`\n
    Raises **FileNotFoundError** if ***LM Studio*** was not accesible via *CLI*\n
    Raises **ConnectionError** if it *ultimately failed* to run ***LM Studio*** on `localhost:1234`
    """
    lms_cli = check_lms()
    if not lms_cli:
        raise FileNotFoundError(f"LM Studio is either not installed OR not added to PATH")
    lms_localhost = check_lms_server()
    if not lms_localhost:
        start_lms_server()
        i = 0
        limit = 7
        while True:
            time.sleep(0.5)
            i += 1
            if not check_lms_server():
                if i == limit:
                    break
                retry = _input(None, normal=True, prompt="Connection failed... retry? [Y/N]")
                if not retry:
                    break
                else:
                    continue
        if not check_lms_server():
            raise ConnectionError("Could not start ***LM Studio*** on `localhost:1234`")

def list_lms() -> None:
    """
    Displays a list of models that the user has installed from LM Studio
    """
    models = requests.get("http://localhost:1234/v1/models", timeout=5)
    models.raise_for_status()
    models = models.json()
    data = models["data"]
    if len(data) == 0:
        print("[bold bright_blue]No models found![/bold bright blue]")
        return
    names = [model["id"] for model in data]
    print("[bold yellow]Installed LM Studio Models:[/bold yellow]")
    for name in names:
        print(f"[bold magenta]>> [/bold magenta][bold bright_green]{name}[/bold bright_green]")

def install_list() -> None:
    """
    Display a list of hand-picked models that support tool calling reliably
    """
    print("[bold yellow]Not all models provided by LM Studio support tool calling reliably.\n"
      "The following is a hand-picked list of models that work well with tools:[/bold yellow]")
    for model in MODELS.keys():
        print(f"[bold magenta]>> [/bold magenta][bold bright_green]{model}[/bold bright_green]")
    print("[bold yellow]Enter the name of a model to install it\nEnter 'Exit' to exit.[/bold yellow]")
    while True:
        print("[bold magenta]>>> [/bold magenta]", end="")
        model_id = input().lower()
        if model_id == "exit":
            sys.exit()
        elif model_id not in MODELS.keys():
            print("[bold red]Not a model![/bold red]")
            continue
        else:
            url = MODELS[model_id]["url"]
            try:
                subprocess.run(["lms", "get", url], check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                error(f"Failed to install '{model_id}'")