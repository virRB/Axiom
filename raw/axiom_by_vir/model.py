import subprocess
import errors
import json
import random
from typing import Any


class ModelSelector:
    """Base class for model-selection strategies accepted by `Model`."""


class PickRandom(ModelSelector):
    """
    Select a random model saved on the user's device.

    Pass the class itself to `Model`, not an instance.

    Raises:
        AxiomNoModelError: If no models are saved on the device.
        SyntaxError: If an instance of this class is created.
    """
    def __init__(_) -> None:
        raise SyntaxError("When using PickRandom, the class itself is meant to be passed, not an instance")


def json_from_cli(*command) -> dict | list:
    """
    Execute an Axiom CLI command and parse its JSON output.

    Args:
        *command: The command and arguments to execute.

    Returns:
        dict | list: The parsed JSON response.

    Raises:
        AxiomNotFoundError: If the Axiom CLI cannot be found.
        AxiomWrongVersion: If the CLI reports an incompatible version.
        AxiomError: If the CLI command fails.
        AxiomJsonReadError: If the CLI output is not valid JSON.
    """
    try:
        response = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=True
        )
    except FileNotFoundError:
        raise errors.AxiomNotFoundError("Could not reach Axiom via CLI")
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 1:
            raise errors.AxiomWrongVersion("The Axiom python API requires Axiom v>=v1.1.0") from exc
        raise errors.AxiomError("Axiom CLI Failed") from exc
    try:
        return json.loads(response.stdout)
    except json.JSONDecodeError:
        raise errors.AxiomJsonReadError("Could not parse JSON provided by Axiom CLI")


class Response:
    """Represent a response returned by an Axiom model."""
    def __init__(self: Response, **kwargs: Any) -> None:
        """
        Initialise a response with dynamically assigned attributes.

        Keyword arguments become accessible instance attributes.

        Args:
            **kwargs: Attribute names and their corresponding values.

        Attributes:
            attributes: A tuple containing the names of the supplied
                keyword arguments.
        """
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.attributes = tuple(kwargs.keys())


class Model:
    """Represent a saved Axiom model that can generate responses."""

    def __init__(self: Model, name: str | type[ModelSelector]) -> None:
        """
        Initialise a model by name or using a selection strategy.

        Args:
            name: The name of a saved model, or `PickRandom` to select
                a random saved model.

        Raises:
            AxiomJsonReadError: If the CLI model list is not a list.
            AxiomModelNotFoundError: If the specified model does not exist.
            AxiomNoModelError: If `PickRandom` is used with no saved models.
        """
        devls_json = json_from_cli("axiom", "-devls")
        if not isinstance(devls_json, list):
            raise errors.AxiomJsonReadError(f"Expected -devls to return a list, however \"{type(devls_json).__name__}\" was recieved")
        if isinstance(name, str):
            if name not in devls_json:
                raise errors.AxiomModelNotFoundError(f'"{name}" was not found as a saved Axiom model')
        elif name == PickRandom:
            if len(devls_json) == 0:
                raise errors.AxiomNoModelError("No Axiom models are saved on this device")
            name = random.choice(devls_json)
        self.model = name
    def ask(self: Model, prompt: str) -> Response:
        """
        Send a prompt to the model and return its response.

        Args:
            prompt: The message or question to send to the model.

        Returns:
            Response: An object containing the response message, number
                of steps taken, and model name.

        Raises:
            AxiomRespondError: If the response indicates failure or
                cannot be interpreted.
        """
        response = json_from_cli("axiom", "--ask", self.model, prompt)
        if response["status"] == "failed":
            raise errors.AxiomRespondError("Axiom failed to generate a response")
        elif response["status"] == "complete":
            return Response(
                message=response["content"],
                steps=response["steps"],
                model=self.model
            )
        else:
            raise errors.AxiomRespondError("Could not read Axiom --ask output")
