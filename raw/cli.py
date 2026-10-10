import sys
import argparse
import os
from compiler import compile_model
from run import model_class_from_model_name
from rich import print
import asyncio
import tool_api
import builtins
import json
from paths import MODELS
from stuff import done, error
from no_handwritten_json import magic_stuff
import lms

CWD = os.getcwd()

def _api() -> tool_api.API:
    """
    Wrapper around creation of the API
    """
    return tool_api.API(cwd=CWD)
async def _main():
    """
    # Main
    """
    parser = argparse.ArgumentParser(prog="axiom")
    parser.add_argument("--compile", "-c", type=str, metavar=("<model-name>", "<file-name>"), help="Store a model from a given ZIP file", nargs=2)
    parser.add_argument("--run", "-r", type=str, metavar="<model-name>", help="Run a stored model")
    parser.add_argument("--ask", "-a", type=str, metavar=("<model-name>", "<prompt>"), help="Ask a model a question and get the response in JSON stdout", nargs=2)
    parser.add_argument("--list", "-ls", action="store_true", dest="ls", help="List all created models")
    parser.add_argument("--create", "-cr", action="store_true", help="Create a model directly in terminal without having to manually write JSON")
    parser.add_argument("--list-lms", "-lslms", action="store_true", help="List all available models from LM Studio")
    parser.add_argument("--list-good-models", "-lsgmod", action="store_true", help="Display a list of hand-picked models that Axiom can easily support, and allow the user to install them")
    args = parser.parse_args()
    args_n = [
        "run",
        "compile",
        "ask",
        "ls",
        "create",
        "list_lms",
        "list_good_models"
    ]
    if all(not getattr(args, arg) for arg in args_n):
        parser.print_help()
        sys.exit(1)
    if args.compile:
        name, file = args.compile
        file = os.path.join(CWD, file)
        try:
            model_dir = compile_model(name, file)
        except Exception as e:
            error(e)
        done(f"Saved to \"{model_dir}\"")
        done("Model JSON is valid")
    elif args.run:
        name = args.run
        api = _api()
        try:
            agent = model_class_from_model_name(name, api=api)
        except Exception as e:
            error(e)
        print(f"[bold yellow]{name}[/bold yellow]\n{'-'*(len(name)*2)}")
        while True:
            print("[bold magenta]>>> [/bold magenta]", end="")
            prompt = input()
            if prompt.lower() == "exit":
                sys.exit()
            try:
                response = await agent.ask(prompt)
            except Exception as e:
                error(e)
            if "content" in response:
                builtins.print(f"{name}: {response['content']}")
            elif "reason" in response and "status" in response:
                print(f"{response['status']}: {response['reason']}")
            else:
                print("No content was found...")
    elif args.ask:
        model, prompt = args.ask
        api = _api()
        try:
            agent = model_class_from_model_name(model, api=api)
            response = await agent.ask(prompt)
            response["status"] = "complete"
            builtins.print(json.dumps(response))
            sys.exit(0)
        except Exception as e:
            e_struct = {
                "status": "failed",
                "content": str(e)
            }
            builtins.print(json.dumps(e_struct))
            sys.exit(1)
    elif args.ls:
        models = os.listdir(MODELS)
        if len(models) == 0:
            print("[bold bright_blue]No models found![/bold bright_blue]")
            sys.exit()
        for model in models:
            print(f"[bold magenta]>> [/bold magenta][bold bright_green]{model}[/bold bright_green]")
        sys.exit()
    elif args.create:
        try:
            magic_stuff()
        except Exception as e:
            error(e)
    elif args.list_lms:
        try:
            lms.confirm_lms()
            lms.list_lms()
        except Exception as e:
            error(e)
    elif args.list_good_models:
        try:
            lms.confirm_lms()
            lms.install_list()
        except Exception as e:
            error(e)

def entry_point() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    entry_point()