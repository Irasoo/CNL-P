from src.linter.linter._linter import Linter
from src.linter.llm.chatgpt import create_prompt_section, create_llm_client
from dotenv import dotenv_values

import os
import json


class CNLPDataloader:
    def __init__(self, tasks_dir: str, task_filename: str):
        with open(os.path.join(tasks_dir, task_filename), 'r', encoding='utf-8') as file:
            self.json_data = json.load(file)

        self.instances = self.json_data['instance']
        self.total_instances = len(self.instances)

    def get_total_instances(self):
        return self.total_instances

    def get_instance_iterator(self):
        for instance in self.instances:
            yield {
                "id": instance['id'],
                "agent_name": instance['agent_name'],
                "global_variable": instance['global_variable'],
                "api_info": instance['api_info'],
                "schema": instance['schema'],
                "cnlp": instance['cnlp'],
                "reference_version": instance['reference_version']
            }


def check_cnlp_by_llm(global_variable: str, api_info: str, type_info: str, cnlp: str):
    chat_client = create_llm_client(vals=dotenv_values())
    system_prompt = f"""
    1. What is CNLP
    CNLP is a structured language that combines features of natural language with programming language characteristics. It is used to define the behavior and workflow of interactive intelligent agents. CNLP describes an agent's role, tasks, workflows, API calls, etc., enabling the agent to perform complex logic operations.

    CNLP consists of the following main parts:
    - DEFINE_AGENT: Defines the agent, including its role (Persona), constraints, data types, variables, and workflow.
    - DEFINE_PERSONA: Describes the agent’s role and function.
    - DEFINE_CONSTRAINTS: Specifies any constraints on the agent’s behavior.
    - DEFINE_TYPES: Describes data types, including simple types (e.g., '[]' can represent the 'list' type), enumerations, and structured types.
    - DEFINE_VARIABLES: Annotates variables used by the agent for reference only. It can include both global variables and variables temporarily defined in the Instruction section. The type of a global variable can be set as 'UnKnown' (since global variables have real values). The actual use of the variables is determined by the INSTRUCTION section.
    - DEFINE_WORKER: Defines the agent's workflow, including inputs, outputs, the main logic flow (MAIN_FLOW), and commands (COMMANDS)。
    - ABOUT_COMMAND: "There are four types of commands: 'CALL' for calling APIs where the 'response' keyword is used as needed to handle return values; 'INPUT' for requesting user input, which must use the 'VALUE' keyword to store the input in a variable; 'COMMAND' as a regular command type that may use the 'RESULT' keyword to manage variable modifications; and 'DISPLAY' for printing content to the terminal, able to display variables of any type. The first three types can declare new temporary variables using 'var_name: var_type' or reassign existing ones using '<REF>var_name</REF>', but they cannot re-declare variables with the same name."

    2. Differences Between Global and Temporary Elements in CNLP
    In CNLP, elements can be categorized as either global or temporary, applying to variables, types, and APIs:

    - Global Elements:
      - Global variables and global types are predefined in the backend system and can be referenced in any CNLP instance, remaining consistent across different instances.
      - APIs are strictly global and must be predefined; no CNLP instance can define new APIs.

    - Temporary Elements:
      - Temporary variables and types are defined and used only within the current CNLP instance. They are usually declared in DEFINE_TYPES and DEFINE_VARIABLES and are not accessible in other CNLP instances.

    Note: Although DEFINE_VARIABLES lists variables, the actual usage is determined by the INSTRUCTION section.

    3. All Possible Error Types in CNLP and Their Explanation
    To ensure CNLP correctness, here are all potential error types, each with an explanation:

    3.1 Reference-Related Errors
    - 3.1.1 Referencing Non-Existent Global Variables: Referring to variables not defined globally. For example, referencing <REF>_user_preference</REF> in the PERSONA section when it doesn't exist globally.
    - 3.1.2 Using Undeclared Variables: Using variables in the workflow that are not declared in DEFINE_VARIABLES or globally.
    - 3.1.3 Duplicate Variable Declaration: Declaring the same variable multiple times with inconsistent types.
    - 3.1.4 Variables Undefined in Conditional Branches: Variables may not be properly defined or assigned in some branches of IF/ELSEIF/ELSE, leading to issues later.

    3.2 Type-Related Errors
    - 3.2.1 Target Type Not Found: Using a type that hasn't been defined in DEFINE_TYPES or the global schema.
    - 3.2.2 API Parameter Type Mismatch: Passing parameters to an API with types that do not match the API's expected types. When the parameter is a global variable with an unknown type, it should be compared with the defined value type.
    - 3.2.3 API Return Type Mismatch: The type of the API's return value doesn't match the type of the receiving variable.

    3.3 API Call-Related Errors
    - 3.3.1 Calling Non-Existent APIs: Attempting to call an API that is not defined in the global API list.
    - 3.3.2 Extraneous API Parameters: Providing more parameters than the API definition requires.
    - 3.3.3 Missing API Parameters: Failing to provide all necessary parameters for an API call.
    - 3.3.4 Unhandled API Return Values: API returns a result, but it is not stored or processed.
    - 3.3.5 Improper Handling of API Return Values: Attempting to capture a return value from an API that doesn’t return any.

    3.4 Global Variable Conflict Errors
    - 3.4.1 Global Variable Naming Conflicts: Defining a local variable with the same name as a global variable, causing potential overwriting or conflict.

    4. Error Return Format
    Only a list of dictionaries containing two key fields: error_path and error_reason should be returned.

    Important: The error_path can only be one of the following sections: PERSONA, CONSTRAINTS, or INSTRUCTION. It should not point to errors within DEFINE_VARIABLES or DEFINE_TYPES, as these sections are for display purposes and not directly related to execution logic.

    Error Path Explanation
    The error path identifies where the error occurs in the CNLP instance, including but not limited to:
    - persona.ROLE: Indicates an error in the persona definition.
    - instruction.main_flow.if_block1.command4: Indicates an error in the 4th command within if_block1 in the main flow instruction.

    Error Return Format Example:

    If an error occurs in the PERSONA section:
    Example CNLP:
    ROLE: You are a news assistant looking up various current events, the specific task information is subject to <REF>_user_preferences</REF>.
    If _user_preferences is undeclared, the error would be:

    [
        {{
            "error_path": "persona.ROLE.reference1",
            "error_reason": "The variable '_user_preferences' referenced in <REF>_user_preferences</REF> is not declared in the DEFINE_VARIABLES section or globally."
        }}
    ]

    5. Background Data
    - Global Variable: {global_variable}
    - API Information (If the API description lacks a return statement, it means the API doesn't return any value): {api_info}
    - Global Type(s): {type_info}
    """

    messages = [
        create_prompt_section(role="system", content=system_prompt),
        create_prompt_section(role="user", content=cnlp)
    ]
    return chat_client.complete(messages)


def check_cnlp_by_linting(cnlp):
    compiler = Linter(cnlp=cnlp)
    compiler.syntax_analysis()
    compiler.semantic_analysis()
    return compiler.error_management.error_sum()


