from tools import CNLPDataloader, check_cnlp_by_llm, check_cnlp_by_linting

import pandas as pd
import os
from datetime import datetime

tasks_dir = os.path.join(os.path.dirname(__file__), 'tasks')

task_list = [
    "task001_persona_referenced_global_variable_does_not_exist.json",
    "task002_constraint_referenced_global_variable_does_not_exist.json",
    "task003_undeclared_variable_reference.json",
    "task004_duplicate_variable_declaration.json",
    "task005_conditional_branch_scope_issue.json",
    "task006_target_type_cannot_be_found.json",
    "task007_api_call_argument_type_mismatch.json",
    "task008_api_return_type_mismatch.json",
    "task009_non_existent_api.json",
    "task010_extraneous_api_parameters.json",
    "task011_missing_api_parameters.json",
    "task012_unhandled_api_return_value.json",
    "task013_unexpected_api_return_handling.json",
    "task014_global_variable_naming_conflict.json"
]

llm_results = []
linting_results = []

for task_filename in task_list:
    cnlp_dataloader = CNLPDataloader(tasks_dir=tasks_dir, task_filename=task_filename)
    print(task_filename)

    for instance_info in cnlp_dataloader.get_instance_iterator():
        instance_id = instance_info['id']
        global_variable = instance_info['global_variable']
        api_info = instance_info['api_info']
        global_types = instance_info['schema']
        cnlp = instance_info['cnlp']
        reference_version = instance_info['reference_version']

        llm_result = check_cnlp_by_llm(global_variable=global_variable, api_info=api_info, type_info=global_types,
                                      cnlp=cnlp)
        linting_result = check_cnlp_by_linting(cnlp=cnlp)

        llm_results.append({
            "task_filename": task_filename,
            "instance_id": instance_id,
            "agent_name": instance_info['agent_name'],
            "global_variable": global_variable,
            "api_info": api_info,
            "type_info": global_types,
            "reference_version": reference_version,
            "cnlp_code": cnlp,
            "llm_errors": llm_result
        })

        linting_results.append({
            "task_filename": task_filename,
            "instance_id": instance_id,
            "agent_name": instance_info['agent_name'],
            "global_variable": global_variable,
            "api_info": api_info,
            "type_info": global_types,
            "reference_version": reference_version,
            "cnlp_code": cnlp,
            "linting_errors": linting_result
        })

llm_df = pd.DataFrame(llm_results)
linting_df = pd.DataFrame(linting_results)

llm_df['Correct Location Identified (CLI)'] = ""
llm_df['Correct but Erroneous Explanation (CEE)'] = ""
llm_df['Explanation with Redundant Misjudgment (ERM)'] = ""

linting_df['Correct Location Identified (CLI)'] = ""
linting_df['Correct but Erroneous Explanation (CEE)'] = ""
linting_df['Explanation with Redundant Misjudgment (ERM)'] = ""

result_dir = "./result"
os.makedirs(result_dir, exist_ok=True)


current_time = datetime.now().strftime("%Y%m%d_%H%M")
llm_output_path = os.path.join(result_dir, f"llm_error_summary_{current_time}.csv")
linting_output_path = os.path.join(result_dir, f"linting_error_summary_{current_time}.csv")

llm_df.to_csv(llm_output_path, index=False, encoding='utf-8')
linting_df.to_csv(linting_output_path, index=False, encoding='utf-8')

print(f"The result has been saved to {os.path.abspath(llm_output_path)}")
print(f"The result has been saved to {os.path.abspath(linting_output_path)}")
