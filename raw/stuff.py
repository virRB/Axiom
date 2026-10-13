"""
Pretty terminal output for errors and completions
"""

from rich import print
import sys

def error(e: str) -> None:
    """
    Print an error message in yellow with a red cross\n
    Also ends the script
    """
    print(f"[bold red]✗[/bold red][bold yellow] {e}[/bold yellow]")
    sys.exit(1)

def done(d: str) -> None:
    """
    Print a completion message in bright blue with a green checkmark
    """
    print(f"[bold bright_green]✓[/bold bright_green][bold bright_blue] {d}[/bold bright_blue]")

def _input(name: str, normal: bool=False, prompt: str|None=None) -> bool:
    """
    Special input that accepts only 'y' or 'n', designed for confirming the use of unsafe tools.\n
    'normal' lets you use this with a custom prompt, as long as 'prompt' is also specified.
    """
    while True:
        if not normal:
            confirm = input(f"The agent wants to use the '{name}' tool.\nAccept? [Y/N]").lower()
        else:
            confirm = input(prompt)
        if confirm == "y":
            return True
        elif confirm == "n":
            return False