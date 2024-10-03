import re
import json
from dotenv import dotenv_values
from typing import TypedDict, List, Dict, Generator, Any
from src.linter.llm.chatgpt import Chatgpt, create_prompt_section, create_llm_client
from src.linter.linter.error_management import Error


class Token(TypedDict):
    token_type: str
    token_value: str


class Parser:
    __slots__ = (
        "chat_client",
        "cnlp_blocks_name",
        "cnlp_blocks",
        "cnlp_ast_like",
        "cnlp_temp_types"
    )

    def __init__(self, env: dict):
        self.chat_client = create_llm_client(vals=env)
        self.cnlp_blocks_name: List[str] = ["PERSONA", "CONSTRAINTS", "WORKER", "TYPES", "VARIABLES"]
        self.cnlp_blocks = None
        self.cnlp_ast_like = {}
        self.cnlp_temp_types = {}

    def extract_cnlp_blocks(self, cnlp: str) -> Dict[str, str]:
        """
        Extracts the content of each block from the given CNLP string and returns a dictionary containing these block contents.

        :param cnlp: type is str, a string containing the CNLP content.
        :return cnlp_blocks: type is Dict[str, str], a dictionary where the keys are the block names (in lowercase) and the values are the corresponding block contents.
        """
        cnlp_blocks = {}
        lines = cnlp.split('\n')

        for element_name in self.cnlp_blocks_name:
            elements = []
            current_start_mark = f"[DEFINE_{element_name}:"
            current_end_mark = f"[END_{element_name}]"
            capturing_element = False

            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith(current_start_mark):
                    capturing_element = True
                    elements.append(line + "\n")
                elif stripped_line.startswith(current_end_mark):
                    elements.append(line + "\n")
                    break  # Break out of the loop once the end marker is found.
                elif capturing_element:
                    elements.append(line + "\n")

            current_element_content = ''.join(elements)  # Use join to merge all element contents.
            if element_name == "WORKER":
                element_name = "instruction"
            cnlp_blocks[element_name.lower()] = current_element_content

        return cnlp_blocks

    def syntax_analysis(self, cnlp: str) -> Dict[str, dict | List[Error]]:
        self.cnlp_blocks = self.extract_cnlp_blocks(cnlp=cnlp)
        error_list = []
        for key, value in self.cnlp_blocks.items():
            if key == "persona":
                persona_result = self.persona_syntax_analysis()
                self.cnlp_ast_like['persona'] = persona_result['persona_dict']
                error_list.extend(persona_result['error_list'])
            elif key == "constraints":
                constraint_result = self.constraints_syntax_analysis()
                self.cnlp_ast_like['constraints'] = constraint_result['constraints_dict']
                error_list.extend(constraint_result['error_list'])
            elif key == "instruction":
                instruction_result = self.instruction_syntax_analysis()
                self.cnlp_ast_like['instruction'] = instruction_result
            elif key == "types":
                self.cnlp_temp_types = self.cnlp_type_to_python_schema()

        return {"cnlp_ast_like": self.cnlp_ast_like, "error_list": error_list, "cnlp_temp_types": self.cnlp_temp_types}

    def description_with_reference_syntax_analysis(self, cnlp_sentence: str, block_name: str) -> Dict[
        str, dict | List[Error]]:
        """
        Performs traditional syntax analysis on the DESCRIPTION_WITH_REFERENCE section of CNLP.
        It first checks keywords with lexical tokenization and then constructs the syntax tree.

        :param cnlp_sentence: The original CNLP text to be analyzed.
        :param block_name: The name of the CNLP section to which the analyzed text belongs.
        :return: Returns a dictionary with two keys: {
        "description_dict": dict...
        "error_list": List[Error]
        }
        """

        def description_with_reference_lex(dwr: str) -> Generator[Token, None, None]:
            """
            Tokenizes the DESCRIPTION_WITH_REFERENCE section of CNLP.

            :param dwr: The original CNLP text to be tokenized.
            :return: A generator of Token objects.
            """
            token_specification = [
                ('RefStart', r'<REF>'),
                ('RefEnd', r'</REF>'),
                ('Asterisk', r'\*'),
                ('Str', r'[^\s<>*,?!;]+'),
                ('Punctuation', r'[,.?!;]'),
                ('Space', r' +'),
                ('Newline', r'\n'),
            ]
            token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
            get_token = re.compile(token_regex).match
            match = get_token(dwr)
            while match is not None:
                token_type = match.lastgroup
                token_value = match.group(token_type)  # 'token_value' refers to the specific content of the matched grammatical unit.
                position = match.end()
                yield {"token_type": token_type, "token_value": token_value}
                match = get_token(dwr, position)

        def description_with_reference_parse(tokens: List[Token]) -> Dict[str, List[str] | dict]:
            """
            :param tokens: The sequence of tokens obtained from tokenization.
            :return: Returns a dictionary with two keys:
                     The first key is the CNLP dictionary structure built after token parsing. The other key contains the error reasons.
                     {
                        "description_dict": dict...
                        "error_list": List[Error]
                     }
            """
            error_reason_list = []

            ref_close = True
            description_dict = {}
            ref_descriptions = {}
            current_ref = None
            ref_index = 1
            text_accum = ""
            var_count = 0  # Used to count the number of variables in REF, if greater than 1, an error is reported.
            asterisk = False
            ref_messy = False

            for token in tokens:
                if token['token_type'] == 'RefStart':
                    if ref_close is False:
                        error_reason_list.append("There are confusing variable references in the description")
                        ref_messy = True
                        break
                    ref_close = False
                    if text_accum: # Collect text before the REF tag.
                        description_dict['description'] = description_dict.get('description',
                                                                               '') + text_accum.strip() + f" <reference{ref_index}> "
                        text_accum = ""
                    current_ref = {'asterisk': False}
                elif token['token_type'] == 'RefEnd':
                    if ref_close:
                        error_reason_list.append("There are confusing variable references in the description")
                        ref_messy = True
                        break
                    if asterisk:
                        current_ref['asterisk'] = True
                    ref_descriptions[f'reference{ref_index}'] = current_ref
                    ref_index += 1
                    current_ref = None
                    var_count = 0
                    asterisk = False
                    ref_close = True
                    if text_accum:  # Ensure any accumulated text is processed after the reference ends.
                        text_accum = ""  # Clear accumulated text.
                elif token['token_type'] == 'Asterisk':
                    if current_ref is not None:
                        asterisk = True
                    else:
                        text_accum += token['token_value']
                elif token['token_type'] in ['Punctuation', 'Space']: # Accumulate text including spaces.
                    text_accum += token['token_value']
                elif token['token_type'] == "Str":
                    if current_ref:
                        if var_count > 0:
                            error_reason_list.append("Too many variables are referenced at once")
                        else:
                            current_ref['var_name'] = token['token_value']
                            var_count += 1
                    else:
                        text_accum += token['token_value']
            if text_accum: # Process the final text or accumulated text.
                description_dict['description'] = description_dict.get('description', '') + text_accum.strip()

            if ref_close is False or ref_messy:
                error_reason_list.append(f"Messy variable references")
            description_dict.update(ref_descriptions)  # Merge all reference information into the main dictionary.

            return {'error_reason_list': error_reason_list, 'description_dict': description_dict}

        tokens = list(description_with_reference_lex(dwr=cnlp_sentence))
        parse_result = description_with_reference_parse(tokens=tokens)
        error_list = []
        for error_reason in parse_result['error_reason_list']:
            error_list.append(
                Error(
                    error_block_name="persona",
                    error_type="syntax",
                    error_sentence=cnlp_sentence,
                    error_reason=error_reason
                )
            )

        return {"description_dict": parse_result['description_dict'], "error_list": error_list}

    def persona_syntax_analysis(self) -> Dict[str, dict | List[dict]]:
        """
        Performs syntax analysis on the PERSONA section, checks for syntax errors, and ultimately constructs the CNLP_AST.

        :return: type is 'Dict[str, dict | list[dict]]', containing the Json representation of the PERSONA section and a list of errors.
        """

        def persona_lex(cnlp: str) -> Generator[Token, None, None]:
            """
            对CNLP的PERSONA描述进行分词

            :param cnlp: 被分词的CNLP原文
            :return: 一个Token的生成器
            """
            token_specification = [
                ('DefinePersona', r'\[DEFINE_PERSONA:\]'),  # Matches the start marker
                ('EndPersona', r'\[END_PERSONA\]'),  # Matches the end marker
                ('RoleAspectStart', r'(ROLE|role):'),  # Matches the role start
                ('AspectStart', r'\b[A-Za-z0-9_]+:'),  # Matches the attribute start, e.g., FOCUS:
                ('Newline', r'\n'),  # Matches the newline character
                ('Text', r'[^\n\s]+'),  # Matches text that is not special characters
                ('Space', r'[ \t]+'),  # Matches spaces and tabs
            ]
            token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
            get_token = re.compile(token_regex).match
            match = get_token(cnlp)
            while match is not None:
                token_type = match.lastgroup
                token_value = match.group(token_type)
                yield {"token_type": token_type, "token_value": token_value}
                match = get_token(cnlp, match.end())

        def persona_parse(cnlp_sentence: str, tokens: List[Token]) -> Dict[str, List[str] | dict]:
            """
                :param tokens: The sequence of tokens obtained from tokenization.
                :return: Returns a dictionary with two keys: the first key is the CNLP dictionary structure built after token parsing, and the other key contains the error reasons.
            """
            error_list = []

            persona_dict = {}
            current_attr = None
            buffer = []
            define_persona_found = False
            end_persona_found = False
            role_found = False
            new_line = True

            for token in tokens:
                if token['token_type'] == 'DefinePersona':
                    define_persona_found = True
                elif token['token_type'] == 'EndPersona':
                    end_persona_found = True
                    if current_attr and buffer:
                        # Pass the accumulated text of the last attribute to the compilation function.
                        dwr_result = self.description_with_reference_syntax_analysis(
                            cnlp_sentence=''.join(buffer).strip(),
                            block_name="persona"
                        )
                        persona_dict[current_attr] = dwr_result['description_dict']
                        error_list.extend(dwr_result['error_list'])
                    break
                elif token['token_type'] in ['RoleAspectStart', 'AspectStart']:
                    if token['token_type'] == 'RoleAspectStart':
                        role_found = True
                    if new_line is not True:
                        buffer.append(token['token_value'])
                    else:
                        if current_attr:
                            if buffer:
                                all_is_space = all(v.isspace() for v in buffer)
                                if all_is_space:
                                    persona_dict[
                                        current_attr] = f"Attribute '{current_attr}' missing effective description with reference."
                                    error = Error(
                                        error_block_name="persona",
                                        error_sentence=cnlp_sentence,
                                        error_type="syntax",
                                        error_reason=f"Attribute '{current_attr}' missing effective description with reference."
                                    )
                                    error_list.append(error)
                                else:
                                    # print(''.join(buffer).strip())
                                    dwr_result = self.description_with_reference_syntax_analysis(
                                        cnlp_sentence=''.join(buffer).strip(),
                                        block_name="persona"
                                    )
                                    persona_dict[current_attr] = dwr_result['description_dict']
                                    error_list.extend(dwr_result['error_list'])
                                    buffer = []
                            else:
                                persona_dict[
                                    current_attr] = f"Attribute '{current_attr}' missing effective description with reference."
                                error = Error(
                                    error_block_name="persona",
                                    error_sentence=cnlp_sentence,
                                    error_type="syntax",
                                    error_reason=f"Attribute '{current_attr}' missing effective description with reference."
                                )
                                error_list.append(error)
                        current_attr = token['token_value'][:-1]  # Set the current attribute and remove the colon.
                        new_line = False
                elif token['token_type'] == 'Text' or token['token_type'] == 'Space':
                    buffer.append(token['token_value'])  # Accumulate text.
                elif token['token_type'] == 'Newline':
                    new_line = True

            # 检查是否存在必要的标记
            if not define_persona_found:
                error = Error(
                    error_block_name="persona",
                    error_type="syntax",
                    error_sentence=cnlp_sentence,
                    error_reason="Missing keyword: [DEFINE_PERSONA:]"
                )
                error_list.append(error)
            if not end_persona_found:
                error = Error(
                    error_block_name="persona",
                    error_type="syntax",
                    error_sentence=cnlp_sentence,
                    error_reason="Missing keyword: [END_PERSONA:]"
                )
                error_list.append(error)
            if not role_found:
                error = Error(
                    error_block_name="persona",
                    error_type="syntax",
                    error_sentence=cnlp_sentence,
                    error_reason="Missing required attribute: 'ROLE'"
                )
                error_list.append(error)

            return {"persona_dict": persona_dict, "error_list": error_list}

        tokens = list(persona_lex(cnlp=self.cnlp_blocks['persona']))
        parse_result = persona_parse(tokens=tokens, cnlp_sentence=self.cnlp_blocks['persona'])

        return parse_result

    def constraints_syntax_analysis(self) -> Dict[str, dict | List[dict]]:
        """
        Performs syntax analysis on the CONSTRAINTS section, checks for syntax errors, and ultimately constructs the CNLP_AST.

        :return: type is 'Dict[str, dict | list[dict]]', containing the Json representation of the CONSTRAINTS section and a list of errors.
        """

        def constraints_lex(cnlp: str) -> Generator[Token, None, None]:
            """
                Tokenizes the CONSTRAINTS description of CNLP.

                :param cnlp: The original CNLP text to be tokenized.
                :return: A generator of Token objects.
            """
            token_specification = [
                ('DefineConstraint', r'\[DEFINE_CONSTRAINTS:\]'),
                ('EndConstraint', r'\[END_CONSTRAINTS\]'),
                ('AspectStart', r'\b[A-Za-z0-9_]+:'),
                ('Newline', r'\n'),
                ('Text', r'[^\n\s]+'),
                ('Space', r'[ \t]+'),
            ]
            token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
            get_token = re.compile(token_regex).match
            match = get_token(cnlp)
            while match is not None:
                token_type = match.lastgroup
                token_value = match.group(token_type)
                yield {"token_type": token_type, "token_value": token_value}
                match = get_token(cnlp, match.end())

        def constraints_parse(cnlp_sentence: str, tokens: List[Token]) -> Dict[str, List[str] | dict]:
            """
            :param tokens: The sequence of tokens obtained from tokenization.
            :return: Returns a dictionary with two keys: the first key is the CNLP dictionary structure built after token parsing, and the other key contains the error reasons.
            """
            error_list = []

            constraints_dict = {}
            current_attr = None
            buffer = []  # 用于累积当前属性的文本
            define_constraints_found = False
            end_constraints_found = False
            new_line = True

            for token in tokens:
                if token['token_type'] == 'DefineConstraint':
                    define_constraints_found = True
                elif token['token_type'] == 'EndConstraint':
                    end_constraints_found = True
                    if current_attr and buffer:
                        dwr_result = self.description_with_reference_syntax_analysis(
                            cnlp_sentence=''.join(buffer).strip(),
                            block_name="constraints"
                        )
                        constraints_dict[current_attr] = dwr_result['description_dict']
                        error_list.extend(dwr_result['error_list'])
                    break
                elif token['token_type'] == 'AspectStart':
                    if new_line is not True:
                        buffer.append(token['token_value'])
                    else:
                        if current_attr:
                            if buffer:
                                all_is_space = all(v.isspace() for v in buffer)
                                if all_is_space:
                                    constraints_dict[
                                        current_attr] = f"Attribute '{current_attr}' missing effective description with reference."
                                    error = Error(
                                        error_block_name="constraints",
                                        error_sentence=cnlp_sentence,
                                        error_type="syntax",
                                        error_reason=f"Attribute '{current_attr}' missing effective description with reference."
                                    )
                                    error_list.append(error)
                                else:
                                    dwr_result = self.description_with_reference_syntax_analysis(
                                        cnlp_sentence=''.join(buffer).strip(),
                                        block_name="constraints"
                                    )
                                    constraints_dict[current_attr] = dwr_result['description_dict']
                                    error_list.extend(dwr_result['error_list'])
                                    buffer = []  # 清空缓冲区
                            else:
                                constraints_dict[
                                    current_attr] = f"Attribute '{current_attr}' missing effective description with reference."
                                error = Error(
                                    error_block_name="constraints",
                                    error_sentence=cnlp_sentence,
                                    error_type="syntax",
                                    error_reason=f"Attribute '{current_attr}' missing effective description with reference."
                                )
                                error_list.append(error)
                        current_attr = token['token_value'][:-1]
                        new_line = False
                elif token['token_type'] == 'Text' or token['token_type'] == 'Space':
                    buffer.append(token['token_value'])
                elif token['token_type'] == 'Newline':
                    new_line = True

            if not define_constraints_found:
                error = Error(
                    error_block_name="constraints",
                    error_type="syntax",
                    error_sentence=cnlp_sentence,
                    error_reason="Missing keyword: [DEFINE_CONSTRAINTS:]"
                )
                error_list.append(error)
            if not end_constraints_found:
                error = Error(
                    error_block_name="constraints",
                    error_type="syntax",
                    error_sentence=cnlp_sentence,
                    error_reason="Missing keyword: [END_CONSTRAINTS:]"
                )
                error_list.append(error)

            return {"constraints_dict": constraints_dict, "error_list": error_list}

        tokens = list(constraints_lex(cnlp=self.cnlp_blocks['constraints']))
        parse_result = constraints_parse(tokens=tokens, cnlp_sentence=self.cnlp_blocks['constraints'])

        return parse_result

    def instruction_syntax_analysis(self):

        system_content = """You are a program that converts Structured Prompt Language (SPL) to a string in JSON format.
You will act as both the lexer and the parser during the compilation process, aiming to construct a JSON string structure similar to an Abstract Syntax Tree (AST). You must also adhere strictly to the integrity of the source text during tokenization and AST construction. It is imperative to preserve the original features of the natural language descriptions, variable names, and type names without any alteration.
Pay close attention to the names of each variable! Sometimes two variable names are extremely identical, such as "info_" and "_info".Be careful.
Direct return string without '```json', '```' and so on, The result will be used directly as an argument to the json.loads function

Next are some conversion methods and json string structure specifications.
'''
1. Define Worker Block (DEFINE_WORKER):
   Each DEFINE_WORKER block should be converted into a worker object with attributes including the worker's name, inputs, outputs, main process, and possible alternative processes.

2. Variable Reference:
   Referenced variables are enclosed in <REF> [*]var_name </REF>, with a need to determine the presence of '*'.
   Conversion format:
   "reference<serial_number>": {
       "asterisk": true or false,
       "var_name": "var_name",
   }

3. Description with Variable Reference (description_with_reference):
   If the description does not contain a reference, omit the reference and keep only the description text.
   Example description:
   "this is a <REF> _example </REF> to show with <REF> * _sb </REF>"
   Conversion result:
   {
       "description": "this is a reference1 to show with reference2.",
       "reference1": {
           "asterisk": false,
           "var_name": "_example"
       },
       "reference2": {
           "asterisk": true,
           "var_name": "_sb"
       },
   }

4. All conditions are of type description_with_reference.

5. Inputs (INPUTS) and Outputs (OUTPUTS):
   All variables in INPUT are referenced global variables.
   Variables in OUTPUT can only be those introduced in the INPUT or temporary variables created in the MAIN_FLOW.

6. Process Includes Required Main Flow, Zero or More Alternative Flows, and Zero or One Exception Flow:
   All flows have the same indentation level in the JSON string.
   Alternative and exception flows must include respective conditions.
   Each flow contains zero or more BLOCKS.
   Blocks of each type in each FLOW can contain more than one and cannot be merged
   Conversion format:
   {
       "worker": "worker_name",
       "input": {...},
       "output": {...},
       "main_flow": {...},
       "alternative_flow": {
           "condition": {...},
           ...
       },
       "exception_flow": {
           "condition": {...},
           ...
       }
   }

7. Blocks in the Process (BLOCK):
   Each process can contain various types of BLOCKS, each capable of holding zero or more commands. Specific types include:

   SEQUENTIAL_BLOCK:
       - Each sequential_block must have a decision index for naming.
       - Contains zero or more commands.

   IF_BLOCK:
       - Each if_block must have a decision index for naming.
       - Structure includes a unique "if_part", zero or more "elif_parts", and a unique "else_part".
       - Each "if_part" or "elif_part" must include a condition.
       - Each part contains zero or more commands.
       - Example conversion format:
           "alternative_flow": {                                                                             
               "if_block<serial_number>": {
                   "if_part": {
                       "condition": {...},
                       "command1": {...}, 
                       "command2": {...},
                       ...
                   "elif_part1": {
                       "condition": {...},
                       "command1": {...}, 
                       "command2": {...},
                       ...
                   },
                   "elif_part2": {
                       "condition": {...},
                       "command1": {...}, 
                       "command2": {...},
                       ...
                    },
                    ...
                   "else_part": {
                       "command1": {...}, 
                       "command2": {...},
                       ...
                   }
               }
           }

   WHILE_BLOCK:
       - Contains zero or more commands.
       - Similar to IF_BLOCK, includes a decision index.
       - Contains a while condition.
       - Example conversion format:
           "alternative_flow": {
               "while_block": {
                   "condition": {...},
                   "command1": {...}, 
                   "command2": {...},
                   ...
               }
           }

   FOR_BLOCK:
       - Contains zero or more commands.
       - Similar to IF_BLOCK, follows the same naming rules and decision index.
       - Contains a for condition.
       - Example conversion format:
           "alternative_flow": {
               "for_block": {
                   "condition": {...},
                   "command1": {...}, 
                   "command2": {...},
                   ...
               }
           }

8. Definition and Structure of Commands:
   Each command consists of a command_index and a command_body, with the command_index being globally unique within the worker.
   The command_body types include general_command, call_api, display_message and request_input.

   - Example of general_command:
     Input format BNF: GENERAL_COMMAND := "[COMMAND" DESCRIPTION_WITH_REFERENCES ["RESULT" COMMAND_RESULT ["SET" | "APPEND"]] "]"
     Conversion format:
     "command<serial_number>": {
         "type": "general_command",
         "description_with_reference": {...},
         "result": {
            # When creating a new variable, declare the variable name and type as follows.
             "var_name": "var_name",
             "var_type": "var_type",
            # When you operate on an existing variable, you refer to it as follows:
             "reference<serial_number>": {
                "asterisk": true or false,
                "var_name": "var_name",
             },
            # Use the 'SET' operation when reassigning a variable. However, when the variable is of type 'list' or 'dict' and you need to add content to it, employ the 'APPEND' operation.
             "operation": "SET" | "APPEND",
         }
     }
   - Example of call_api:
     Input format BNF: CALL_API := "[CALL" API_NAME ["WITH" ARGUMENT_LIST] ["RESPONSE" COMMAND_RESULT ["SET" | "APPEND"]] "]"
     Conversion format:
     "command<serial_number>": {
         "type": "call_api",
         "api_name": "api_name",
         "paras": {
             "parameter": "argument",
             ...
         },
         "response": {
            # When creating a new variable, declare the variable name and type as follows.
             "var_name": "var_name",
             "var_type": "var_type",
            # When you operate on an existing variable, you refer to it as follows:
             "reference<serial_number>": {
                "asterisk": true or false,
                "var_name": "var_name",
             },
            # Use the 'SET' operation when reassigning a variable. However, when the variable is of type 'list' or 'dict' and you need to add content to it, employ the 'APPEND' operation.
             "operation": "SET" | "APPEND",
         }
     }
   - Example of request_input:
     Input format BNF: REQUEST_INPUT := "[INPUT" DESCRIPTION_WITH_REFERENCE "VALUE" COMMAND_RESULT ["SET" | "APPEND"] "]"
     Conversion format:
     "command<serial_number>": {
         "type": "request_input",
         "description_with_reference": {...},
         "value": {
            # When creating a new variable, declare the variable name and type as follows.
             "var_name": "var_name",
             "var_type": "var_type",
            # When you operate on an existing variable, you refer to it as follows:
             "reference<serial_number>": {
                "asterisk": true or false,
                "var_name": "var_name",
             },
            # Use the 'SET' operation when reassigning a variable. However, when the variable is of type 'list' or 'dict' and you need to add content to it, employ the 'APPEND' operation.
             "operation": "SET" | "APPEND",
         }
     }
   - Example of display_message:
     Input format BNF: DISPLAY_MESSAGE := "[DISPLAY" DESCRIPTION_WITH_REFERENCES "]"
     Conversion format:
     "command<serial_number>": {
        "type": "display_message",
        "description_with_reference": {...}
'''
"""

        example_input = """[DEFINE_WORKER: Generate_Question]
            [INPUTS]
                <REF> *_topic </REF>
                <REF> _chat_records </REF>
            [END_INPUTS]
            [OUTPUTS]
                <REF> _question </REF>
            [END_OUTPUTS]

            [MAIN_FLOW]
                [SEQUENTIAL_BLOCK]
                    COMMAND-1 [COMMAND Review the list of questions and answers in _chat_records RESULT <REF> _chat_records </REF> SET]
                [END_SEQUENTIAL_BLOCK]
                [IF You have more questions related to <REF> _topic </REF> to ask]
                    COMMAND-2 [INPUT Ask one new question RESULT _temp_data:str SET]
                    COMMAND-3 [CALL data_check WITH source_data:_chat_records, temp_data:_temp_data RESPONSE <REF> _question <REF> SET]
                [END_IF]
                [SEQUENTIAL_BLOCK]
                    COMMAND-4 [DISPLAY show the user about <REF> _chat_records </REF>]
                [END_SEQUENTIAL_BLOCK]
            [END_MAIN_FLOW]

            [ALTERNATIVE_FLOW: No more questions to ask]
                COMMAND-5 [COMMAND Set _question as "No more questions. Thank you so much for your help"]
            [END_ALTERNATIVE_FLOW]
        [END_WORKER]
"""

        example_output = """{
    "worker": "Generate_Question",
    "input": {
        "reference1": {
            "asterisk": true,
            "var_name": "_topic"
        },
        "reference2": {
            "asterisk": false,
            "var_name": "_chat_records"
        }
    },
    "output": {
        "reference3": {
            "asterisk": false,
            "var_name": "_question"
        }
    },
    "main_flow": {
        "sequential_block1": {
            "command1": {
                "type": "general_command",
                "description_with_reference": {
                    "description": "Review the list of questions and answers in reference2.",
                    "reference2": {
                        "asterisk": false,
                        "var_name": "_chat_records"
                    }
                },
                "result": {
                    "reference2": {
                        "asterisk": false,
                        "var_name": "_chat_records"
                    },
                    "operation": "SET"
                }
            }
        },
        "if_block1": {
            "if_part": {
                "condition": {
                    "description": "You have more questions related to reference1 to ask.",
                    "reference1": {
                        "asterisk": true,
                        "var_name": "_topic"
                    }
                },
                "command2": {
                    "type": "request_input",
                    "description_with_reference": {
                        "description": "Ask one new question."
                    },
                    "result": {
                        "var_name": "_temp_data",
                        "var_type": "str",
                        "operation": "SET"
                    }
                },
                "command3": {
                    "type": "call_api",
                    "api_name": "data_check",
                    "paras": {
                        "source_data": "_chat_records",
                        "temp_data": "_temp_data"
                    },
                    "response": {
                        "reference3": {
                            "asterisk": false,
                            "var_name": "_question"
                        },
                        "operation": "SET"
                    }
                }
            },
        "sequential_block2": {
            "command4": {
                "type": "display_message",
                "description_with_reference": {
                    "description": "show the user about reference2.",
                    "reference2": {
                        "asterisk": false,
                        "var_name": "_chat_records"
                    }
                }
            },
        },
    },
    "alternative_flow": {
        "condition": {
            "description": "No more questions to ask."
        },
        "command5": {
            "type": "general_command",
            "description_with_reference": {
                "description": "Set _question as 'No more questions. Thank you so much for your help.'"
            }
        }
    }
} 
"""

        actual_input = self.cnlp_blocks['instruction']

        messages = [
            create_prompt_section(role="system", content=system_content),
            create_prompt_section(role="user", content=example_input),
            create_prompt_section(role="assistant", content=example_output),
            create_prompt_section(role="user", content=actual_input)
        ]
        response = self.chat_client.complete(messages)
        instruction_json = json.loads(response)

        return instruction_json

    def cnlp_type_to_python_schema(self):

        system_content = """Convert the following type descriptions into corresponding Python schema.

Assume that all necessary types from the `typing` module have already been imported.

Required format: Return the output strictly in a single JSON format, representing the Python types without any additional textual explanations or comments. The structure should follow the example provided below, where each key is a type name and each value is the corresponding Python code for that type.

For simple types like "int", "float", "dict", "list", "str", there is no need to use the contents of the typing module.

Direct return string without '```json', '```' and so on, The result will be used directly as an argument to the json.loads function

Output example:
{
    "example_type1": "example_type1 = Literal['a', 'b', 'c', ...]",
    "example_type2": "example_type2 = Dict[str, int]",
    "example_type3": "example_type3 = dict",
    "example_type4": "example_type4 = int",
    ...
}        
        """
        actual_input = self.cnlp_blocks['types']
        messages = [
            create_prompt_section(role="system", content=system_content),
            create_prompt_section(role="user", content=actual_input)
        ]
        response = self.chat_client.complete(messages)
        types_json = json.loads(response)

        return types_json



    def print_dict(self, indent=0, data=None):
        if data is None:
            if self.cnlp_blocks:
                data = self.cnlp_ast_like
            else:
                print("Try again after parsing.")
                return None

        for key, value in data.items():
            if isinstance(value, dict):
                print(' ' * indent + str(key) + ':')
                self.print_dict(indent=indent + 4, data=value)
            else:
                print(' ' * indent + str(key) + ': ' + str(value))


if __name__ == "__main__":
    def error_default(o):
        if isinstance(o, Error):
            return o.to_dict()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


    cnlp = """
    [DEFINE_AGENT: Daily News helper]
        [DEFINE_PERSONA:]
            ROLE: You are a news assistant looking up various current events, according to <REF> *test test2 </REF>.
            FUNCTION: Call various apis to get JSON messages, and convert JSON data into text information for display.
        [END_PERSONA]

        [DEFINE_CONSTRAINTS:]
            FORBID: It is necessary to filter the query message to avoid the illegal content of bloody violence and pornography and keep the information positive and healthy
        [END_CONSTRAINTS]

        [DEFINE_WORKER: Obtain and report information]
            [INPUTS]
                <REF> user_account1 </REF>
            [END_INPUTS]
            
            [OUTPUTS] 
                <REF> _report_info </REF>
            [END_OUTPUTS]

            [MAIN_FLOW]
                [SEQUENTIAL_BLOCK]
                    COMMAND-1 [INPUT Ask the user what type(game, finance, sport, movie, weather, google_news) of information they want and record the user's response VALUE _request_type: str SET]
                [END_SEQUENTIAL_BLOCK]
                [IF _request_type is google_news]
                    COMMAND-2 [CALL get_google_news WITH user: user_account1 RESPONSE json_info:dict SET]
                [ELSEIF _request_type is game]
                    COMMAND-3 [INPUT Ask the user for the keywords they want to search for VALUE _search_words:str SET]
                    COMMAND-4 [CALL get_game_data WITH user: user_account1 search_words:_search_words RESPONSE json_info:dict SET]
                [ELSEIF _request_type is movie]
                    COMMAND-5 [CALL get_movie_data WITH user: user_account1 RESPONSE json_info:dict SET]
                [ELSEIF _request_type is finance]
                    COMMAND-6 [CALL get_finance_data WITH user: user_account1 RESPONSE json_info:dict SET]
                [ELSEIF _request_type is sport]
                    COMMAND-7 [CALL get_sport_data WITH user: user_account1 RESPONSE json_info:dict SET]
                [ELSEIF _request_type is weather]
                    COMMAND-8 [CALL get_weather_data WITH user: user_account1 RESPONSE json_info:dict SET]
                [ELSE]
                    COMMAND-9 [DISPLAY Can not provide the relevant type of news]
                [ENDIF]
                [SEQUENTIAL_BLOCK]
                    COMMAND-10 [CALL transform_json_news WITH json_data:json_info RESPONSE _report_info:str SET]
                    COMMAND-11 [DISPLAY Displays the processed json information <REF> _report_info </REF]
                [END_SEQUENTIAL_BLOCK]  
            [END_MAIN_FLOW]

        [END_WORKER]
    [END_AGENT]    
    """

    spl2 = """
    [DEFINE_AGENT: DailyNewsHelper "The Daily News Helper is a news assistant whose primary responsibility is to find and provide the latest news information based on user requests."]
        [DEFINE_PERSONA:]
            ROLE: The Daily News Helper is a news assistant whose primary responsibility is to find and provide the latest news information based on user requests.
            Function: This assistant calls various APIs to obtain JSON-formatted messages and converts these messages into easily understandable text information to display to the user.
        [END_PERSONA]

        [DEFINE_CONSTRAINTS:]
            ContentFiltering: When processing queries, the assistant must filter the input to ensure that it excludes any content related to violence, bloodshed, or pornography, ensuring that all provided information is positive and healthy.
        [END_CONSTRAINTS]

        [DEFINE_TYPES:]
            RequestType = ["game", "finance", "sport", "movie", "weather", "Google News"]
        [END_TYPES]

        [DEFINE_VARIABLES:]
            _user_account1: str
            _request_type: RequestType
            _search_words: str
            json_info: 
            _report_info: str
        [END_VARIABLES]

        [DEFINE_WORKER: "Workflow to handle user requests and display news information" NewsWorkflow]
            [INPUTS]
                <REF>_user_account1</REF>
            [END_INPUTS]

            [OUTPUTS]
                <REF>_report_info</REF>
            [END_OUTPUTS]

            [MAIN_FLOW]
                [SEQUENTIAL_BLOCK]
                    COMMAND-1 [INPUT "What type of information do you need? (game, finance, sport, movie, weather, Google News)" VALUE _request_type: RequestType SET]
                [END_SEQUENTIAL_BLOCK]

                [IF <REF>_request_type</REF> = "Google News"]
                    COMMAND-2 [CALL get_google_news WITH {user: <REF>_user_account1</REF>} RESPONSE json_info: JsonInfo SET]
                [ELSEIF <REF>_request_type</REF> = "game"]
                    COMMAND-3 [INPUT "Please enter the keywords you want to search for." VALUE _search_words: str SET]
                    COMMAND-4 [CALL get_game_data WITH {user: <REF>_user_account1</REF>, search_words: <REF>_search_words</REF>} RESPONSE json_info: JsonInfo SET]
                [ELSEIF <REF>_request_type</REF> = "movie"]
                    COMMAND-5 [CALL get_movie_data WITH {user: <REF>_user_account1</REF>} RESPONSE json_info: dict SET]
                [ELSEIF <REF>_request_type</REF> = "finance"]
                    COMMAND-6 [CALL get_finance_data WITH {user: <REF>_user_account1</REF>} RESPONSE json_info: JsonInfo SET]
                [ELSEIF <REF>_request_type</REF> = "sports"]
                    COMMAND-7 [CALL get_sport_data WITH {user: <REF>_user_account1</REF>} RESPONSE json_info: JsonInfo SET]
                [ELSEIF <REF>_request_type</REF> = "weather"]
                    COMMAND-8 [CALL get_weather_data WITH {user: <REF>_user_account1</REF>} RESPONSE json_info: JsonInfo SET]
                [ELSE]
                    COMMAND-9 [DISPLAY "Sorry, we cannot provide the relevant type of news."]
                [END_IF]

                [SEQUENTIAL_BLOCK]
                    COMMAND-10 [CALL transform_json_news WITH {json_data: <REF>json_info</REF>} RESPONSE _report_info: str SET]
                    COMMAND-11 [DISPLAY <REF>_report_info</REF>]
                [END_SEQUENTIAL_BLOCK]
            [END_MAIN_FLOW]
        [END_WORKER]
    """
    parser = Parser(env=dotenv_values())
    result = parser.syntax_analysis(cnlp=cnlp)
    print(json.dumps(result['cnlp_ast_like'], indent=4))
    print(json.dumps(result['error_list'], indent=4))
    print(json.dumps(result['cnlp_temp_types'], indent=4))





