"""
The Exceptions used by Axiom
"""

class AxiomError(Exception):
    """
    Base class for all exceptions raised by Axiom\n
    (Exception)
    """

class AxiomModelError(AxiomError):
    """
    Base class for all exceptions raised by Axiom concerning Models\n
    (AxiomError)
    """

class AxiomNotFoundError(AxiomError):
    """
    Raised when Axiom was not found via CLI\n
    (AxiomError)
    """

class AxiomWrongVersion(AxiomError):
    """
    Raised when an older/unsupported version of Axiom is installed\n
    (AxiomError)
    """

class AxiomModelNotFoundError(AxiomModelError):
    """
    When the provided model was not found\n
    (AxiomModelError)
    """

class AxiomNoModelError(AxiomModelError):
    """
    When no usable Axiom model was found\n
    (AxiomModelError)
    """

class AxiomInvalidModelError(AxiomModelError):
    """
    When the model provided is not a valid Axiom model\n
    (AxiomModelError)
    """

class AxiomInternalError(AxiomError):
    """
    Base class for all exceptions concering an internal mistake or oversight in Axiom's source code\n
    (AxiomError)
    """

class AxiomJsonReadError(AxiomInternalError):
    """
    When Axiom cannot read the JSON provided by the Axiom CLI\n
    (AxiomInternalError)
    """

class AxiomRespondError(AxiomModelError):
    """
    When Axiom fails to respond to a prompt provided by --ask\n
    (AxiomModelError)
    """