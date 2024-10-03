import os
from datetime import datetime
import pandas as pd
from dotenv import dotenv_values
from tools import DataLoader, LLM, to_cnlp_system_content, to_rodes_system_content, to_risen_system_content

tasks_dir = r"../../natural-instructions/tasks"

SOCIAL_GOOD_TASK_IDS = [
    'task137_',
    'task327_', 'task333_', 'task335_', 'task337_',
    'task905_',
    'task320_',  # prompt formatted-ish, classification
    'task1502_', 'task1503_', 'task1504_',  # no prompt format: classification, classification, generation
    'task1664_',  # no prompt format: set of words as output
    'task1669_', 'task1670_',  # no prompt format, long generation but well defined!
    'task1720_', 'task1725_',  # no prompt format, binary classification
    'task904_',  # no prompt format, classification,
    'task277_', 'task278_', 'task279_', 'task280_', 'task316_', 'task317_', 'task318_', 'task319_', 'task320_',
    'task321_',
    'task108_',
    'task322_', 'task323_', 'task324_', 'task325_', 'task326_', 'task327_', 'task328_',
    'task1604_', 'task1605_', 'task1606_', 'task1607_',
    'task1721_', 'task1722_', 'task1723_', 'task1724_',
    'task607_', 'task608_', 'task609_', 'task286_'
]

SUPERNATURAL_INSTRUCTIONS_TASKS_WITH_NO_FORMAT = [
    'task1502_', 'task1503_', 'task1504_',  # no prompt format: classification, classification, generation
    'task1664_',  # no prompt format: set of words as output
    'task1669_', 'task1670_',  # no prompt format, long generation but well defined!
    'task1720_', 'task1725_',  # no prompt format, binary classification
    'task904_',  # no prompt format, classification
    'task108_',
    'task1604_', 'task1605_', 'task1606_', 'task1607_',
    'task1721_', 'task1722_', 'task1723_', 'task1724_',
    'task607_', 'task608_', 'task609_', 'task286_',
    'task1149_', 'task1189_'
]

FORMATTED_MULTIPLE_CHOICE_SUPERNATURAL_INSTRUCTIONS_TASKS = [  # ends up being one-field format
    'task065_', 'task1297_', 'task084_', 'task697_', 'task729_',
    'task1380_', 'task1381_', 'task309_', 'task1431_', 'task220_', 'task1612_', 'task190_', 'task1347_',
    'task069_', 'task070_',
    'task137_', 'task138_', 'task139_', 'task140_', 'task296_', 'task297_', 'task118_', 'task1135_',
    'task1424_', 'task1423_', 'task1422_', 'task1421_', 'task1420_', 'task1419_',
    'task1678_', 'task385_', 'task580_', 'task214_', 'task213_'
]

FORMATTED_TWO_TEXT_FIELDS_SUPERNATURAL_INSTRUCTIONS_TASKS = ['task1661_', 'task027_', 'task136_', 'task021_', 'task018_', 'task020_', 'task740_',
     'task1366_', 'task1162_', 'task1587_', 'task491_', 'task492_', 'task050_', 'task1387_',
     'task1186_', 'task1283_', 'task1284_', 'task905_', 'task501_']

FORMATTED_ONE_TEXT_FIELDS_SUPERNATURAL_INSTRUCTIONS_TASKS = [
    'task155_', 'task158_', 'task161_', 'task163_', 'task162_', 'task322_', 'task323_',
    'task324_', 'task325_', 'task326_', 'task327_', 'task328_', 'task333_', 'task335_',
    'task337_', 'task277_', 'task278_', 'task279_', 'task280_', 'task316_', 'task317_',
    'task113_', 'task114_']

max_tokens = 4000
gpt_models = ['gpt-4o-mini-2024-07-18', 'gpt-4o']  # gpt-4o gpt-4o-mini-2024-07-18
llama_models = ['llama3-70b-8192']


env_values = dotenv_values('../../.env')
gpt_key = env_values.get('OPENAI_API_KEY')
llama_key = env_values.get('GROQ_API_KEY')
gpt = LLM(gpt_key)
llama = LLM(llama_key)


def to_cnlp(input: str):
    return gpt.query(model="gpt-4o-2024-08-06", messages=LLM.get_msg(prompt=to_cnlp_system_content, user_input=input))


def to_risen(input: str):
    return gpt.query(model="gpt-4o-2024-08-06", messages=LLM.get_msg(prompt=to_risen_system_content, user_input=input))


def to_rodes(input: str):
    return gpt.query(model="gpt-4o-2024-08-06", messages=LLM.get_msg(prompt=to_rodes_system_content, user_input=input))

def predict_instance(used_model, llm, instance_input, definition, cnlp_definition, risen_definition, rodes_definition):
    nl_messages = LLM.get_msg(prompt=definition, user_input=instance_input, user_role_need=False)
    cnlp_messages = LLM.get_msg(prompt=cnlp_definition, user_input=instance_input, user_role_need=False)
    risen_messages = LLM.get_msg(prompt=risen_definition, user_input=instance_input, user_role_need=False)
    rodes_messages = LLM.get_msg(prompt=rodes_definition, user_input=instance_input, user_role_need=False)

    nl_output = llm.query(used_model, nl_messages)
    cnlp_output = llm.query(used_model, cnlp_messages)
    risen_output = llm.query(used_model, risen_messages)
    rodes_output = llm.query(used_model, rodes_messages)

    return nl_output, cnlp_output, risen_output, rodes_output


def run_tasks(tasks: list, instance_num: int, used_model: str):
    print("Testing tasks:", tasks)

    if used_model in gpt_models:
        llm = gpt
    elif used_model in llama_models:
        llm = llama

    dataloader = DataLoader(tasks_dir=tasks_dir, instance_num=instance_num)
    for task in tasks:
        print(f'Start testing {task}...')
        definition_list = []
        result_list = []
        accuracy_list = []

        task_content = dataloader.get_task_content_random(task_filename=task)
        definition = task_content['definition'][0]
        _definition = "".join(['Please convert the following user requirement to corresponding prompt:\n', definition])
        instances = task_content['instances']
        # instances = dataloader.load_saved_instances(task)

        def extract_definition(text):
            import re
            matches = re.findall(r'```(.*?)```', text, re.DOTALL)
            if matches:
                return matches[0].strip()
            else:
                return text

        definition_generator = {
            'to_cnlp': to_cnlp,
            'to_risen': to_risen,
            'to_rodes': to_rodes,
        }

        definitions = {'original': definition, 'cnlp': '', 'risen': '', 'rodes': ''}
        for definition_name in definitions.keys():
            if definition_name != 'original':
                generate = definition_generator[f'to_{definition_name}']
                definition_content = extract_definition(generate(_definition))
                definitions[definition_name] = definition_content
            definition_list.append({
                "task_name": task,
                "type": definition_name,
                "content": definitions[definition_name]
            })

        nl_correct_count = 0
        cnlp_correct_count = 0
        risen_correct_count = 0
        rodes_correct_count = 0

        for index, instance in enumerate(instances):
            instance_input = instance['input']
            standard_output = ','.join(instance['output'])

            nl_output, cnlp_output, risen_output, rodes_output = predict_instance(used_model=used_model, instance_input=instance_input,
                                                                                 llm=llm, definition=definition,
                                                                                 cnlp_definition=definitions['cnlp'],
                                                                                 risen_definition=definitions['risen'],
                                                                                 rodes_definition=definitions['rodes'])

            if cnlp_output == standard_output:
                cnlp_correct_count += 1
            if nl_output == standard_output:
                nl_correct_count += 1
            if risen_output == standard_output:
                risen_correct_count += 1
            if rodes_output == standard_output:
                rodes_correct_count += 1

            result_list.append({
                'task_name': task,
                'instance_id': index + 1,
                'instance_content': instance_input,
                'standard_output': standard_output,
                'nl_output': nl_output,
                'nl_score': None,
                'cnlp_output': cnlp_output,
                'cnlp_score': None,
                'risen_output': risen_output,
                'risen_score': None,
                'rodes_output': rodes_output,
                'rodes_score': None,
            })

        cnlp_accuracy = cnlp_correct_count / instance_num
        nl_accuracy = nl_correct_count / instance_num
        risen_accuracy = risen_correct_count / instance_num
        rodes_accuracy = rodes_correct_count / instance_num

        accuracy_list.append({
            'task_name': task,
            'nl_accuracy': nl_accuracy,
            'cnlp_accuracy': cnlp_accuracy,
            'risen_accuracy': risen_accuracy,
            'rodes_accuracy': rodes_accuracy,
        })

        definition_df = pd.DataFrame(definition_list)
        result_df = pd.DataFrame(result_list)
        accuracy_df = pd.DataFrame(accuracy_list)

        result_dir = "./result"
        os.makedirs(result_dir, exist_ok=True)

        current_time = datetime.now().strftime("%Y%m%d_%H%M")

        definition_path = os.path.join(result_dir,
                                       f"{task}definition_instance{instance_num}_tokens{max_tokens}_{current_time}.csv")
        result_path = os.path.join(result_dir,
                                   f"{task}result_{used_model}_instance{instance_num}_tokens{max_tokens}_{current_time}.csv")
        accuracy_path = os.path.join(result_dir,
                                     f"{task}accuracy_{used_model}_instance{instance_num}_tokens{max_tokens}_{current_time}.csv")

        definition_df.to_csv(definition_path, index=False, encoding='utf-8')
        result_df.to_csv(result_path, index=False, encoding='utf-8')
        accuracy_df.to_csv(accuracy_path, index=False, encoding='utf-8')

        print('=' * 100 + '\n', definition_path, '\n', result_path, '\n', accuracy_path, '\n', '=' * 100 )
        print(f'{task} has been completed by model {used_model}.\n')

    print(f"The model {used_model} has complete all the tasks:", tasks)


if __name__ == '__main__':
    instance_num = 1
    tasks = ['task190_', 'task385_', 'task729_', 'task1162_', 'task1424_', 'task1678_']
    used_models = ['gpt-4o-mini-2024-07-18', 'gpt-4o', 'llama3-70b-8192']
    for model in used_models:
        run_tasks(tasks, instance_num, model)
