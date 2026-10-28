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

from prompt_toolkit import PromptSession
import prompt_toolkit.styles
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.lexers import Lexer

Style = prompt_toolkit.styles.Style.from_dict({
    "prompt": "bold magenta",
    "exit-command": "bold red",
    "help-command": "bold blue",
    "clear-command": "bold magenta"
})

Session: PromptSession|None = None
class AxiomLexer(Lexer):
    def lex_document(self, document):
        def get_line(line_number):
            line = document.lines[line_number]
            text = document.text.strip().lower()

            if text == "exit":
                return [("class:exit-command", line)]
            elif text == "help":
                return [("class:help-command", line)]
            elif text == "forget":
                return [("class:clear-command", line)]

            return [("", line)]

        return get_line

async def fancy_input(prompt: str) -> str:
    global Session
    if Session is None:
        Session = PromptSession()
    return await Session.prompt_async([("class:prompt", prompt)], lexer=AxiomLexer(), style=Style)