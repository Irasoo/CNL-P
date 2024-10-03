from src.linter.linter.nodevisitor.type_validator import TypeValidator, create_instance, get_types_from_string
from src.linter.linter.nodevisitor.result import Success, Failure, Result
from src.data import schema
from src.data.apis.description import apis_description
from src.data.vars.description import vars_description
from src.linter.linter.error_management import Error

import fnmatch
from typing import TypedDict, Dict, List, Union, Optional, Any, Literal

"""
{
    "main_control_flow": {
        "sequential_block1": {
            "block_order": 1,
            "commands": {
                "command1": 1
            }
        },
        "if_block1": {
            "block_order": 2,
            "total_branch": 6,
            "if_part": {
                "commands": {
                    "command2": 1
                }
            },
            "elif_part1": {
                "commands": {
                    "command3": 1,
                    "command4": 2
                }
            },
            "elif_part2": {
                "commands": {
                    "command5": 1
                }
            },
            "elif_part3": {
                "commands": {
                    "command6": 1
                }
            },
            "elif_part4": {
                "commands": {
                    "command7": 1
                }
            },
            "elif_part5": {
                "commands": {
                    "command8": 1
                }
            },
            "else_part": {
                "commands": {
                    "command9": 1
                }
            }
        },
        "sequential_block2": {
            "block_order": 3,
            "commands": {
                "command10": 1,
                "command11": 2
            }
        }
    }
}


"var_not_in_if_block": {
    "block_order": int,
    "total"
    "command_order": int,
}

"var_in_if_block": {
    "block_order": int,
    "total_branch": int,
    "command_order":{
        "if_part": int,
        ...
    }
}
"""


class CommandPosition(TypedDict):
    block_order: int
    total_branch: Optional[int]
    command_order: Union[int, Dict[str, int]]

class SpecialPosition(TypedDict):
    special_type: Literal['input', 'output', 'persona', 'constraints']

class Path(TypedDict):
    area: str
    flow: str
    block: str
    branch: Optional[str]  # Enable this only when the block type is 'IF_BLOCK'
    command: str


class TempVar(TypedDict):
     type: str
     is_global: bool
     value: Optional[Any]
     source: str
     append_position: CommandPosition


def parse_path(path: str) -> Path | None | SpecialPosition:
    path_parts = path.split('.')

    command_index = None
    branch = None

    # Find the first section containing 'command'
    for i, part in enumerate(path_parts):
        if "input" in part:
            return SpecialPosition(special_type="input")
        elif "output" in part:
            return SpecialPosition(special_type="output")
        elif "persona" in part:
            return SpecialPosition(special_type="persona")
        elif "constraints" in part:
            return SpecialPosition(special_type="constraints")
        elif "condition" in part:
            command_index = i
        elif "command" in part:
            command_index = i
            break

    if command_index is None:
        return None

    # If there is a branch section, it is the section before the command
    if command_index == 4:
        branch = path_parts[command_index - 1]

    return Path(
        area=path_parts[0],
        flow=path_parts[1],
        block=path_parts[2],
        branch=branch,
        command=path_parts[command_index]
    )


def match_path_to_control_flow(path: Path | SpecialPosition, control_flow) -> Optional[CommandPosition] | SpecialPosition:
    if 'special_type' in path:
        return path

    try:
        block = path['block']
        branch = path.get('branch')
        command = path['command']
    except:
        return None

    # 检查block是否存在
    if block in control_flow:
        block_data = control_flow[block]

        # 对于sequential_block
        if 'commands' in block_data:
            commands = block_data['commands']
            if command in commands:
                return CommandPosition(
                    block_order=block_data['block_order'],
                    total_branch=None,
                    command_order=commands[command]
                )

        # 对于if_block
        elif branch:
            if branch in block_data:
                branch_data = block_data[branch]
                if command in branch_data['commands']:
                    return CommandPosition(
                        block_order=block_data['block_order'],
                        total_branch=block_data.get('total_branch'),
                        command_order={branch: branch_data['commands'][command]}
                    )
                elif command == "condition":
                    return CommandPosition(
                        block_order=block_data['block_order'],
                        total_branch=block_data.get('total_branch'),
                        command_order={branch: 0}
                    )
    return None


class VarManagement:
    """
    self.global_vars 是一个保存了全局变量的字典结构：
        其中每一个键值对中，键名就是 变量名， 键值则是该变量包含的一些信息
        其示意结构如下：


    self.temp_vars 是一个保存了临时变量的字典结构
        其中每一个键值对中，键名就是 变量名， 键值则是该变量包含的一些信息
        其事以结构如下：
    """
    def __init__(self, variables):  # 修改参数名以避免潜在的命名冲突
        self.global_vars = {var_name: var_info for var_name, var_info in variables.items()}
        self.temp_vars: Dict[str, TempVar] = {}

    def variable_existence_check(self, to_check_var: Dict[str, str | CommandPosition | None | SpecialPosition]) -> Result:
        """
        参数to_check_var的结构：
        {
            'var_name': str,
            'command_position': {


        :param to_check_var:
        :return:
        """
        for global_var_name, global_var in self.global_vars.items():
            if global_var_name == to_check_var['var_name']:
                return Success("The global variable exists!")
        if 'special_type' in to_check_var['command_position']:
            special_type = to_check_var['command_position']['special_type']
            if special_type in ["input", "persona", "constraints"]:
                return Failure(f"This variable '{to_check_var['var_name']}' is not declared")
            elif special_type == "output":
                result = self.get_var(var_name=to_check_var['var_name'])
                if isinstance(result, Failure):
                    return Failure(f"This variable '{to_check_var['var_name']}' is not declared")
                else:
                    return Success(None)
        for temp_var_name, temp_var in self.temp_vars.items():
            if temp_var_name == to_check_var['var_name']:
                # 开始比较作用域，先判断变量的首次声明是否在IF_BLOCK中
                # 如果变量的首次声明在IF_BLOCK中
                if temp_var['append_position']['total_branch']:
                    if temp_var['append_position']['block_order'] > to_check_var['command_position']['block_order']:
                        return Failure(f"The reference to the variable {temp_var_name} was made before its declaration.")
                    # 如果对于此变量的引用和申明处在同一个IF_BLOCK中，则首先要确定变量申明的分支中是否有此次进行引用的分if分支
                    elif temp_var['append_position']['block_order'] == to_check_var['command_position']['block_order']:
                        # 如果引用分支在申明分支中，还需要进入深入的比较
                        ref_branch = next(iter(to_check_var['command_position']['command_order']))
                        if ref_branch in temp_var['append_position']['command_order']:
                            # 如果在此分支中，引用在申明之前，则报错
                            if temp_var['append_position']['command_order'][ref_branch] > to_check_var['command_position']['command_order'][ref_branch]:
                                return Failure(f"The reference to the variable {temp_var_name} was made before its declaration.")
                            else:
                                return Success('References to variables are reasonable')
                        else:
                            return Failure('The variable is declared only in other branches of the same IF_BLOCK.')
                    # 当添加位置的block_order比此次引用前，
                    else:
                        branch_num = len(temp_var['append_position']['command_order'])
                        if branch_num == temp_var['append_position']['total_branch']:
                            return Success('References to variables are reasonable')
                        else:
                            return Failure(f"The variable '{temp_var_name}' is used without being conditionally declared in all branches of the IF_BLOCK.")
                else:
                    if temp_var['append_position']['block_order'] < to_check_var['command_position']['block_order']:
                        return Success('References to variables are reasonable')
                    elif temp_var['append_position']['block_order'] == to_check_var['command_position']['block_order']:
                        if temp_var['append_position']['command_order'] < to_check_var['command_position']['command_order']:
                            return Success('References to variables are reasonable')
                        else:
                            return Failure(f"The reference to the variable {temp_var_name} was made before its declaration.")
                    else:
                        return Failure(f"The reference to the variable {temp_var_name} was made before its declaration.")
                # 如果temp_var的声明时间比此次引用时间找
        return Failure(f"This variable '{to_check_var['var_name']}' is not declared")

    def append_temp_var(self, temp_var_info: dict) -> Result:
        temp_var_name = temp_var_info['var_name']
        exist_var_info = self.get_var(var_name=temp_var_name)
        # 判断是否已在变变量管理中存在
        if isinstance(exist_var_info, Success):
            # 查看是否为全局变量，如果是则报错 ‘命名冲突’
            if exist_var_info.value['is_global']:
                return Failure("There is a naming conflict due to the existence of globally scoped variables with identical names.")
            # 如果是临时变量，那就做一系列深入的比较
            else:
                if self.temp_vars[temp_var_name]['append_position']['block_order'] < temp_var_info['append_position']['block_order']:
                    return Failure(f"The variable '{temp_var_name}' has already been declared earlier, so the current declaration will not take effect.")
                elif self.temp_vars[temp_var_name]['append_position']['block_order'] == temp_var_info['append_position']['block_order']:
                    if temp_var_info['append_position']['total_branch']:
                        branch = next(iter(temp_var_info['append_position']['command_order']))
                        if branch in self.temp_vars[temp_var_name]['append_position']['command_order']:
                            if self.temp_vars[temp_var_name]['append_position']['command_order']['branch'] > temp_var_info['append_position']['command_order'][branch]:
                                # 其实此处应该改成Warning内容，因为按照顺序来说，前面的声明变量应该会先被记录，按理来说只在主流中分析时不会出现这种情况
                                # 但仍然应该将前面的申明进行重新记录
                                self.temp_vars[temp_var_name]['type'] = temp_var_info['var_type']
                                self.temp_vars[temp_var_name]["append_position"]['command_order']['branch'] = temp_var_info['append_position']['command_order'][branch]
                                return Failure(f"This variable '{temp_var_name}' is redeclared later in the code, but the current declaration will take precedence.")
                            else:
                                return Failure(f"The variable '{temp_var_name}' has already been declared earlier, so the current declaration will not take effect.")
                        else:
                            # 说明在这个if_block中，变量在其他的分支有申明
                            self.temp_vars[temp_var_name]['append_position']['command_order'][branch] = temp_var_info['append_position']['command_order'][branch]
                            return Success("The variable declaration has been noted in this branch.")
                    else:
                        if exist_var_info.value['append_position']['command_order'] < temp_var_info['append_position']['command_order']:
                            return Failure(f"The variable '{temp_var_name}' has already been declared earlier, so the current declaration will not take effect.")
                        else:
                            return Failure(f"This variable '{temp_var_name}' is redeclared later in the code, but the current declaration will take precedence.")
        else:
            self.temp_vars[temp_var_name] = {
                "type": temp_var_info['var_type'],
                "is_global": False,
                "value": None,
                "source": "temporary_creation",
                "append_position": temp_var_info['append_position']
            }

        return Success(f"The temporary variable '{temp_var_info['var_name']}' has been added.")

    def get_var(self, var_name: str) -> Result:
        if var_name in self.global_vars:
            return Success({'var_name': var_name, 'type': self.global_vars[var_name]['type'], 'is_global': True, 'value': self.global_vars[var_name]['value'], "source":self.global_vars[var_name]["source"]})
        if var_name in self.temp_vars:
            return Success({'var_name': var_name, 'type': self.temp_vars[var_name]['type'], 'is_global': False, 'value': self.temp_vars[var_name]['value'], "append_position": self.temp_vars[var_name]["append_position"]})
        return Failure(f"This variable '{var_name}' does not exist.")


class APIManagement:
    """

    """
    def __init__(self, apis):
        self.apis = {api_name: api_info for api_name, api_info in apis.items()}

    def api_existence_check(self, api_name) -> Result:
        for key, value in self.apis.items():
            if key == api_name:
                return Success("The API exists!")
        return Failure(f"The API '{api_name}' does not exist!")

    def get_api_info(self, api_name: str) -> Result:
        if api_name in self.apis:
            return Success(self.apis[api_name])
        return Failure(f"The API '{api_name}' does not exist!")


class NodeVisitor:

    def __init__(self, cnlp_ast_like, cnlp_temp_types):
        self.cnlp_ast_like = cnlp_ast_like
        self.control_flow = {"main_flow": {}}
        self.vars_management = VarManagement(vars_description)
        self.apis_management = APIManagement(apis_description)
        self.cnlp_temp_types = cnlp_temp_types
        self.type_validator = None
        block_order = 1

        def parse_block(block, block_type, block_order):
            parsed_block = {"block_order": block_order}
            command_counter = 1

            if block_type == "sequential_block":
                parsed_block['commands'] = {}
                for command_key, command_value in block.items():
                    parsed_block["commands"][command_key] = command_counter
                    command_counter += 1

            elif block_type == "if_block":
                total_branches = len([key for key in block.keys() if 'part' in key])
                parsed_block["total_branch"] = total_branches
                for part_key, part_value in block.items():
                    if "part" in part_key:
                        part_commands = {}
                        command_counter = 1
                        for command_key, command_value in part_value.items():
                            if command_key.startswith("command"):
                                part_commands[command_key] = command_counter
                                command_counter += 1
                        parsed_block[part_key] = {"commands": part_commands}

            return parsed_block

        for block_key, block_value in self.cnlp_ast_like['instruction']['main_flow'].items():
            if any(keyword in block_key for keyword in ["sequential_block", "while_block", "for_block"]):
                parsed_block = parse_block(block_value, "sequential_block", block_order)
            elif "if_block" in block_key:
                parsed_block = parse_block(block_value, "if_block", block_order)

            self.control_flow["main_flow"][block_key] = parsed_block
            block_order += 1

    def find_keys(self, pattern):
        """
        Searches for keys in the instance dictionary of the class that match the fuzzy matching pattern.

        Parameters: pattern: The fuzzy matching pattern, such as 'reference*' which will match 'reference1', 'reference2', etc.

        Returns: A dictionary where the keys are the full key paths and the values are the corresponding key values.

        Example:
        Suppose self.cnlp_ast_like is as follows:
           {
               "instruction": {
                   "worker": "Obtain and report information",
                   "input": {
                       "reference1": {
                           "asterisk": False,
                           "var_name": "user_account3"
                       }
                   },
                   "output": {
                       "reference2": {
                           "asterisk": False,
                           "var_name": "_report_info"
                       }
                   },
                   "main_flow": {
                       "sequential_block1": {
                           "command1": {
                               "type": "request_input",
                               "description_with_reference": {
                                   "description": "Ask the user what type(game, finance, sport, movie, weather, google_news) of information they want and record the user's response."
                               },
                               "value": {
                                   "var_name": "_request_type",
                                   "var_type": "str",
                                   "operation": "APPEND"
                               }
                           },
                           "command2": {
                               "type": "general_command",
                               "description_with_reference": {
                                   "description": "NL..."
                               },
                               "result": {
                                   "var_name": "json_info",
                                   "var_type": "dict",
                                   "operation": "APPEND"
                               }
                           }
                       },
                       "if_block1": {
                           "if_part": {
                               "condition": {
                                   "description": "_request_type is google_news."
                               },
                               "command2": {
                                   "type": "call_api",
                                   "api_name": "get_google_news",
                                   "paras": {
                                       "user": "user_account1"
                                   },
                                   "response": {
                                       "var_name": "json_info",
                                       "var_type": "dict",
                                       "operation": "SET"
                                   }
                               }
                           },
                           "elif_part1": {
                               "condition": {
                                   "description": "_request_type is game."
                               },
                               "command3": {
                                   "type": "request_input",
                                   "description_with_reference": {
                                       "description": "Ask the user for the keywords they want to search for."
                                   },
                                   "value": {
                                       "var_name": "_search_words",
                                       "var_type": "str",
                                       "operation": "SET"
                                   }
                               },
                               "command4": {
                                   "type": "call_api",
                                   "api_name": "get_game_data",
                                   "paras": {
                                       "user": "user_account1",
                                       "search_words": "_search_words"
                                   },
                                   "response": {
                                       "var_name": "json_info",
                                       "var_type": "dict",
                                       "operation": "SET"
                                   }
                               }
                           },
                           ...
                       },
                       "sequential_block2": {
                           "command10": {
                               "type": "call_api",
                               "api_name": "transform_json_news",
                               "paras": {
                                   "json_data": "json_info"
                               },
                               "response": {
                                   "var_name": "_report_info",
                                   "var_type": "str",
                                   "operation": "APPEND"
                               }
                           },
                           "command11": {
                               "type": "display_message",
                               "description_with_reference": {
                                   "description": "Displays the processed json information reference2.",
                                   "reference2": {
                                       "asterisk": False,
                                       "var_name": "_report_info"
                                   }
                               }
                           }
                       }
                   }
               }
           }

           The return value of calling find_keys("command*"):
           {
               "instruction.main_flow.sequential_block1.command1": { ... },
               "instruction.main_flow.sequential_block1.command2": { ... },
               "instruction.main_flow.if_block1.if_part.command2": { ... },
               "instruction.main_flow.if_block1.elif_part1.command3": { ... },
               "instruction.main_flow.if_block1.elif_part1.command4": { ... },
               "instruction.main_flow.sequential_block2.command10": { ... },
               "instruction.main_flow.sequential_block2.command11": { ... }
           }
        """
        result = {}

        def recurse(data, key_path):
            if isinstance(data, dict):
                for key, value in data.items():
                    new_path = f"{key_path}.{key}" if key_path else key
                    if fnmatch.fnmatch(key, pattern):
                        result[new_path] = value
                    recurse(value, new_path)
            elif isinstance(data, list):
                for index, item in enumerate(data):
                    new_path = f"{key_path}[{index}]"
                    recurse(item, new_path)

        recurse(self.cnlp_ast_like, "")

        return result

    def deal_temp_vars(self) -> Union[List[Error], None] :
        commands = self.find_keys(pattern="command*")
        error_list = []

        for path, command_content in commands.items():
            path_dict = parse_path(path)
            temp_var = {}
            command_position = match_path_to_control_flow(path=path_dict, control_flow=self.control_flow['main_flow'])
            if 'result' in command_content:
                if 'var_name' in command_content['result']:
                    temp_var = {
                        'var_name': command_content['result']['var_name'],
                        'var_type': command_content['result']['var_type'],
                        'append_position': command_position,
                    }
            elif 'response' in command_content:
                if 'var_name' in command_content['response']:
                    temp_var = {
                        'var_name': command_content['response']['var_name'],
                        'var_type': command_content['response']['var_type'],
                        'append_position': command_position,
                    }
            elif 'value' in command_content:
                if 'var_name' in command_content['value']:
                    temp_var = {
                        'var_name': command_content['value']['var_name'],
                        'var_type': command_content['value']['var_type'],
                        'append_position': command_position,
                    }
            if temp_var:
                result = self.vars_management.append_temp_var(temp_var_info=temp_var)
                if isinstance(result, Failure):
                    error_list.append(
                        Error(
                            error_path=path,
                            error_type="semantic",
                            error_block_name="instruction",
                            error_reason=result.message,
                        )
                    )
        return error_list

    def ref_check(self):
        ref_dict = self.find_keys(pattern="reference*")
        error_list = []
        print(ref_dict)
        for path, ref_content in ref_dict.items():
            to_check_var = {}
            path_dict = parse_path(path=path)
            print(path_dict)
            to_check_var['command_position'] = match_path_to_control_flow(path=path_dict, control_flow=self.control_flow['main_flow'])
            to_check_var['var_name'] = ref_content['var_name']
            result = self.vars_management.variable_existence_check(to_check_var=to_check_var)
            if isinstance(result, Failure):
                error_list.append(
                    Error(
                        error_path=path,
                        error_type="semantic",
                        error_block_name="instruction",
                        error_reason=result.message,
                    )
                )

        return error_list

    def call_api_check(self) -> List[Error]:
        """
        1. First, check if the API being called exists.
        2. Check the actual arguments for any unexpected arguments and missing required arguments.
        3. Check the reasonableness of the existence of the arguments being called.
        4. Validate the types of the arguments.
        5. Validate the types of the return values.
        """

        def get_type_from_name(type_name: str):
            basic_types = {
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'list': list,
                'dict': dict
            }
            if type_name in basic_types:
                return basic_types[type_name]
            else:
                # Attempt to retrieve custom types from the schema
                try:
                    return getattr(schema, type_name)
                except AttributeError:
                    pass
                # Attempt to retrieve types from cnlp_temp_types
                if type_name in self.cnlp_temp_types:
                    var_type = self.cnlp_temp_types[type_name]
                    types_namespace = get_types_from_string(var_type)
                    return types_namespace.get(type_name)
            return None

        def variable_type_check(var_name: str, expected_type_name: str, command_position: CommandPosition, existence_check: bool = True) -> Result:
            if existence_check:
                var_existence_result = self.vars_management.variable_existence_check(
                    to_check_var={'var_name': var_name, 'command_position': command_position}
                )
                if isinstance(var_existence_result, Failure):
                    return var_existence_result

            var_info_result = self.vars_management.get_var(var_name=var_name)
            if isinstance(var_info_result, Failure):
                return var_info_result

            var_info = var_info_result.value

            expected_type = get_type_from_name(expected_type_name)
            if expected_type is None:
                return Failure(f"Type '{expected_type_name}' not found.")

            if var_info['is_global']:
                actual_value = var_info['value']
                self.type_validator = TypeValidator(expected_type)
                validate_result = self.type_validator.validate(actual_value)
                if isinstance(validate_result, Failure):
                    return Failure(validate_result.message)
            else:
                actual_type_name = var_info['type']
                actual_type = get_type_from_name(actual_type_name)
                if actual_type is None:
                    return Failure(f"Type '{actual_type_name}' not found.")

                if actual_type != expected_type:
                    # 创建实际类型的实例并验证
                    actual_instance = create_instance(actual_type)
                    if expected_type in [int, float, bool, dict, list, str]:
                        if isinstance(actual_instance, expected_type):
                            pass
                        else:
                            return Failure(
                                f"Variable '{var_name}' is of type '{actual_type_name}', expected '{expected_type_name}'"
                            )
                    self.type_validator = TypeValidator(expected_type)
                    validate_result = self.type_validator.validate(actual_instance)
                    if isinstance(validate_result, Failure):
                        return Failure(f"Variable '{var_name}' is of type '{actual_type_name}', expected '{expected_type_name}'")
            return Success(None)

        error_list = []
        command_dict = self.find_keys(pattern="command*")
        call_dict = {path: content for path, content in command_dict.items() if content.get('type') == "call_api"}

        if not call_dict:
            return error_list

        for path, call_content in call_dict.items():
            path_dict = parse_path(path=path)
            command_position = match_path_to_control_flow(path=path_dict, control_flow=self.control_flow['main_flow'])

            # 检查API是否存在
            api_info_result = self.apis_management.get_api_info(api_name=call_content['api_name'])
            if isinstance(api_info_result, Failure):
                error_list.append(
                    Error(
                        error_path=path,
                        error_type="semantic",
                        error_block_name="instruction",
                        error_reason=api_info_result.message,
                    )
                )
                continue

            api_info = api_info_result.value

            # 检查实参和形参是否匹配
            parameters = set(api_info['paras'].keys())
            arguments = set(call_content['paras'].keys())
            extra_paras = arguments - parameters
            missing_paras = parameters - arguments
            match_paras = parameters & arguments

            if extra_paras:
                error_list.append(
                    Error(
                        error_path=path,
                        error_type="semantic",
                        error_block_name="instruction",
                        error_reason=f"Unexpected parameters found: {', '.join(extra_paras)}",
                    )
                )
            if missing_paras:
                error_list.append(
                    Error(
                        error_path=path,
                        error_type="semantic",
                        error_block_name="instruction",
                        error_reason=f"Missing parameters: {', '.join(missing_paras)}",
                    )
                )

            # 对每个参数进行类型检查
            for match_para in match_paras:
                var_name = call_content['paras'][match_para]
                expected_type_name = api_info['paras'][match_para]
                type_check_result = variable_type_check(
                    var_name=var_name,
                    expected_type_name=expected_type_name,
                    command_position=command_position
                )
                if isinstance(type_check_result, Failure):
                    error_list.append(
                        Error(
                            error_path=path,
                            error_type="semantic",
                            error_block_name="instruction",
                            error_reason=f"Parameter '{match_para}' with argument '{var_name}' has problem: {type_check_result.message}",
                        )
                    )

            # 对返回值进行类型检查
            if api_info.get('return'):
                if call_content.get('response'):
                    response = call_content['response']
                    if response.get('operation') == "SET" and 'var_name' in response:
                        var_name = response['var_name']
                        expected_type_name = api_info['return']
                        type_check_result = variable_type_check(
                            var_name=var_name,
                            expected_type_name=expected_type_name,
                            command_position=command_position,
                            existence_check=False
                        )
                        if isinstance(type_check_result, Failure):
                            error_list.append(
                                Error(
                                    error_path=path,
                                    error_type="semantic",
                                    error_block_name="instruction",
                                    error_reason=f"Response variable '{var_name}' has problem: {type_check_result.message}",
                                )
                            )
                    else:
                        # 如果操作不是 SET，可能不需要检查类型
                        pass
                else:
                    error_list.append(
                        Error(
                            error_path=path,
                            error_type="semantic",
                            error_block_name="instruction",
                            error_reason=f"The function returns a value of type '{api_info['return']}', but no response is set in this command."
                        )
                    )
            else:
                if call_content.get('response'):
                    error_list.append(
                        Error(
                            error_path=path,
                            error_type="semantic",
                            error_block_name="instruction",
                            error_reason="The function does not return a value, but a response is set."
                        )
                    )

        return error_list

    # def command_operation_check(self):
    #     commands = self.find_keys(pattern="command*")
    #     for path, command_content in commands.items():
    #         if 'result' in command_content:
    #
    #         elif 'response' in command_content:
    #             if 'var_name' in command_content['response']:
    #                 temp_var = {
    #                     'var_name': command_content['result']['var_name'],
    #                     'var_type': command_content['result']['var_type'],
    #                     'append_position': command_position,
    #                 }
    #         elif 'value' in command_content:
    #             if 'var_name' in command_content['value']:
    #                 temp_var = {
    #                     'var_name': command_content['result']['var_name'],
    #                     'var_type': command_content['result']['var_type'],
    #                     'append_position': command_position,
    #                 }


if __name__ == "__main__":
    cnlp_ast_like = {
        'persona': {
            'ROLE': {
                'description': 'You are a news assistant looking up various current events.',
            },
            'FUNCTION': {
                'description': 'Call various apis to get JSON messages, and convert JSON data into text information for display.'
            }
        },
        'constraints': {
            'FORBID': {
                'description': 'It is necessary to filter the query message to avoid the illegal content of bloody violence and pornography and keep the information positive and healthy'
            }
        },
        'instruction': {
            'worker': 'Obtain and report information',
            'input': {
                'reference1': {'asterisk': False, 'var_name': 'user_account1'}
            },
            'output': {
                'reference2': {'asterisk': False, 'var_name': '_report_info'}
            },
            'main_flow': {
                'sequential_block1': {
                    'command1': {
                        'type': 'request_input',
                        'description_with_reference': {
                            'description': "Ask the user what type(game, finance, sport, movie, weather, google_news) of information they want and record the user's response."
                        },
                        'value': {
                            'var_name': '_request_type',
                            'var_type': 'str',
                            'operation': 'SET'
                        }
                    }
                },
                'if_block1': {
                    'if_part': {
                        'condition': {'description': '_request_type is google_news.'},
                        'command2': {
                            'type': 'call_api',
                            'api_name': 'get_google_news',
                            'paras': {'user': 'user_account1'},
                            'response': {
                                'var_name': 'json_info',
                                'var_type': 'dict',
                                'operation': 'SET'
                            }
                        }
                    },
                    'elif_part1': {
                        'condition': {'description': '_request_type is game.'},
                        'command3': {
                            'type': 'request_input',
                            'description_with_reference': {
                                'description': 'Ask the user for the keywords they want to search for.'
                            },
                            'value': {
                                'var_name': '_search_words',
                                'var_type': 'str',
                                'operation': 'SET'
                            }
                        },
                        'command4': {
                            'type': 'call_api',
                            'api_name': 'get_game_data',
                            'paras': {'user': 'user_account1', 'search_words': '_search_words'},
                            'response': {
                                'var_name': 'json_info',
                                'var_type': 'dict',
                                'operation': 'SET'
                            }
                        }
                    },
                    'elif_part2': {
                        'condition': {'description': '_request_type is movie.'},
                        'command5': {
                            'type': 'call_api',
                            'api_name': 'get_movie_data',
                            'paras': {'user': 'user_account1'},
                            'response': {
                                'var_name': 'json_info',
                                'var_type': 'dict',
                                'operation': 'SET'
                            }
                        }
                    },
                    'elif_part3': {
                        'condition': {'description': '_request_type is finance.'},
                        'command6': {
                            'type': 'call_api',
                            'api_name': 'get_finance_data',
                            'paras': {'user': 'user_account1'},
                            'response': {
                                'var_name': 'json_info',
                                'var_type': 'dict',
                                'operation': 'SET'
                            }
                        }
                    },
                    'elif_part4': {
                        'condition': {'description': '_request_type is sport.'},
                        'command7': {
                            'type': 'call_api',
                            'api_name': 'get_sport_data',
                            'paras': {'user': 'user_account1'},
                            'response': {
                                'var_name': 'json_info',
                                'var_type': 'dict',
                                'operation': 'SET'
                            }
                        }
                    },
                    'elif_part5': {
                        'condition': {'description': '_request_type is weather.'},
                        'command8': {
                            'type': 'call_api',
                            'api_name': 'get_weather_data',
                            'paras': {'user': 'user_account1'},
                            'response': {
                                'var_name': 'json_info',
                                'var_type': 'dict',
                                'operation': 'SET'
                            }
                        }
                    },
                },
                'sequential_block2': {
                    'command10': {
                        'type': 'call_api',
                        'api_name': 'transform_json_news',
                        'paras': {'json_data': 'json_info'},
                        'response': {
                            'var_name': '_report_info',
                            'var_type': 'str',
                            'operation': 'SET'
                        }
                    },
                    'command11': {
                        'type': 'display_message',
                        'description_with_reference': {
                            'description': 'Displays the processed json information reference2.',
                            'reference2': {'asterisk': False, 'var_name': '_report_info'}
                        }
                    }
                }
            }
        }
    }

    node_visitor = NodeVisitor(
        cnlp_ast_like=cnlp_ast_like,
        cnlp_temp_types=None
    )

    temp_var_errors = node_visitor.deal_temp_vars()
    if temp_var_errors:
        print("Temp var errors found:")
        for error in temp_var_errors:
            print(f"Error Path: {error.error_path}, Reason: {error.error_reason}")
    else:
        print("No temp var errors found.")

    ref_errors = node_visitor.ref_check()
    if ref_errors:
        print("Reference errors found:")
        for error in ref_errors:
            print(f"Error Path: {error.error_path}, Reason: {error.error_reason}")
    else:
        print("No reference errors found.")

    api_errors = node_visitor.call_api_check()
    if api_errors:
        print("API call errors found:")
        for error in api_errors:
            print(f"Error Path: {error.error_path}, Reason: {error.error_reason}")
    else:
        print("No API call errors found.")





