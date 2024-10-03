import json
from typing import TypedDict, Optional, Literal, Dict, List


# class Error(TypedDict):
#     error_section: Literal["persona", "constraints", "instruction"]
#     error_type: Literal["syntax", "semantic"]
#     error_sentence: Optional[str]
#     error_path: Optional[str]
#     error_reason: str


"""
Extensive practice has proven that the CNLP obtained from model conversion rarely contains grammatical errors in most cases.
"""


class Error:
    """
    Represents an error in the CNLP.

    Each error is associated with the following information:
    - The CNLP section the error belongs to (e.g., "PERSONA", "Instruction", etc.).
    - The type of error, which can be "syntax" (grammatical error) or "semantic" (semantic error).
    - The original CNLP statement where the error occurred.
    - The CNLP_json (CNLP AST) path where the error occurred.
    - The specific reason for the error.
    """

    __slots__ = (
        "error_block_name",
        "error_type",
        "error_sentence",
        "error_path",
        "error_reason"
    )

    def __init__(
        self,
        error_block_name: str,
        error_type: Literal["syntax", "semantic"],
        error_reason: str,
        error_sentence: str = None,
        error_path: str = None,
    ):
        if error_type == "syntax" and error_sentence is None:
            raise RuntimeError("Syntax errors should be entered in the corresponding SPL sentence.")

        if error_type == "semantic" and error_path is None:
            raise RuntimeError("Semantic errors should be entered with their corresponding SPL AST path.")

        if error_path is None and error_sentence is None:
            if error_type == "syntax":
                raise RuntimeError("The SPL sentence where the syntax error occurred is missing")
            else:
                raise RuntimeError("The SPL AST path where the semantic error occurred is missing")

        self.error_block_name = error_block_name
        self.error_type = error_type
        self.error_sentence = error_sentence
        self.error_path = error_path
        self.error_reason = error_reason

    def __repr__(self) -> str:
        return (
            f"Error(error_block_name={self.error_block_name!r}, "
            f"error_type={self.error_type!r}, "
            f"error_reason={self.error_reason!r}, "
            f"error_sentence={self.error_sentence!r}, "
            f"error_path={self.error_path!r})"
        )

    def to_dict(self):
        return {
            "error_block_name": self.error_block_name,
            "error_type": self.error_type,
            "error_sentence": self.error_sentence,
            "error_path": self.error_path,
            "error_reason": self.error_reason
        }


class ErrorSet:
    """
    Each section of CNLP has a set of errors responsible for it.
    Each error set in the error set is divided into syntax errors (syntax error) and semantic errors (semantic error).
    Each type of error is stored in a dictionary, where the key is the error statement or error path, and the value is a list storing the specific errors.
    """

    __slots__ = (
        "syntax_errors",
        "semantic_errors",
    )

    def __init__(self):
        self.syntax_errors: Dict[str, List[str]] = {}
        self.semantic_errors: Dict[str, List[str]] = {}

    def append_error(self, error: Error):
        """
        Add a single error to the corresponding type of error dictionary.

        :param error: Type is Error
        :return: None
        """
        # if error.error_sentence in error:
        #     if error.error_sentence in self.syntax_errors:
        #         self.syntax_errors[error.error_sentence].append(error.error_reason)
        #     else:
        #         self.syntax_errors[error.error_sentence] = [error.error_sentence]
        # else:
        #     if error.error_path in self.semantic_errors:
        #         self.semantic_errors[error.error_path].append(error.error_reason)
        #     else:
        #         self.semantic_errors[error.error_path] = [error.error_reason]

        if error.error_type == "syntax":
            if error.error_sentence in self.syntax_errors:
                self.syntax_errors[error.error_sentence].append(error.error_reason)
            else:
                self.syntax_errors[error.error_sentence] = [error.error_sentence]
        elif error.error_type == "semantic":
            if error.error_path in self.semantic_errors:
                self.semantic_errors[error.error_path].append(error.error_reason)
            else:
                self.semantic_errors[error.error_path] = [error.error_reason]
        else:
            raise ValueError(f"Invalid error type '{error.error_type}'.")

    def __repr__(self):
        pass


class ErrorManagement:
    """
    Responsible for centralized management of error sets for each section of SPL: adding errors, checking for the existence of errors, and summarizing errors.

    Structure of the `ErrorManagement` instance:
    ```
    {
        'persona_errors': {
            'syntax_errors': {"error_sentence": [...], ...},
            'semantic_errors': {"error_path": [...], ...}
        },
        'constraints_errors': {
            'syntax_errors': {...},
            'semantic_errors': {...}
        },
        'instruction_errors': {
            'syntax_errors': {...},
            'semantic_errors': {...}
        }
    }
    ```
    """

    __slots__ = (
        "persona_errors",
        "constraints_errors",
        "instruction_errors",
    )

    def __init__(self):
        self.persona_errors = ErrorSet()
        self.constraints_errors = ErrorSet()
        self.instruction_errors = ErrorSet()

    def __add__(self, error: Error):
        match_success = False
        for slot in self.__slots__:
            area_name, x = slot.split('_')
            if error.error_block_name == area_name:
                error_set = getattr(self, slot)
                error_set.append_error(error=error)
                match_success = True
                break
        if not match_success:
            raise ValueError(f"Invalid error section '{error.error_block_name}'")
        return None

    def error_sum(self) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        """
        :return: type is 'Dict[str, Dict[str, Dict[str, List[str]]]]'
        """
        error_summary = {}
        for slot in self.__slots__:
            error_set = getattr(self, slot)
            error_summary[slot] = {
                "syntax_errors": error_set.syntax_errors,
                "semantic_errors": error_set.semantic_errors
            }
        return error_summary

    def has_errors(self) -> bool:
        """
        :return: type is 'bool'
        """
        for slot in self.__slots__:
            error_set = getattr(self, slot)
            if error_set.syntax_errors or error_set.semantic_errors:
                return True
        return False


if __name__ == "__main__":
    error_management = ErrorManagement()

    error1 = Error(
        error_block_name="persona",
        error_type="syntax",
        error_reason="Missing required attribute",
        error_sentence="Persona attribute is not defined"
    )

    error2 = Error(
        error_block_name="constraints",
        error_type="semantic",
        error_reason="Invalid value type",
        error_path="/constraints/0/value"
    )

    error3 = Error(
        error_block_name="instruction",
        error_type="syntax",
        error_reason="Syntax error in instruction format",
        error_sentence="Instruction format is incorrect"
    )

    error_management + error1
    error_management + error2
    error_management + error3

    has_errors = error_management.has_errors()
    print(f"Has errors: {has_errors}")


    error_summary = error_management.error_sum()
    print("Error Summary:")
    print(json.dumps(error_summary, indent=4, ensure_ascii=False))
