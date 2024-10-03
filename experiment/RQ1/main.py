import pandas as pd
import time
import json
import os
import re
from datetime import datetime
from openai import OpenAI
from dotenv import dotenv_values


to_risen_system_content = '''### **Task Overview**
Transform the user's input into a RISEN framework prompt, ensuring each section is clearly defined and accurately reflects the user’s intent.

### **Understanding RISEN**
- Role: [Define the AI's role. E.g., Advisor, Creator]
- Input: [Provide detailed input. E.g., Specific question or topic]
- Steps: [Outline clear steps. E.g., First, provide an overview, then delve into details]
- Expectation: [State your desired outcome. E.g., A comprehensive guide, a brief summary]
- Narrowing: [State any limitations, restrictions, or what to focus on. E.g., word limit, focus on cost-effective options]

### **Conversion Process**
1. **Role**: Identify and specify the role based on the user’s task (e.g., “Advisor,” “Content Creator”).
2. **Input**: Extract the key topics, questions, or data provided by the user.
3. **Steps**: Outline clear, actionable steps the AI should follow, in sequence.
4. **Expectation**: Determine the type of output the user wants.
5. **Narrowing**: Include any constraints, limitations, or specific focus areas.

### **Key Considerations**
- Keep it concise and accurate.
- Ensure each section directly reflects the user’s input.
- Maintain clarity and logical flow.

### **Prompt Architecture**
```
Role: [AI's role, e.g., "Analyst"]

Input: [User's detailed question or topic]

Steps: 
1. [First action]
2. [Next action]
...

Expectation: [Desired outcome]

Narrowing: [Any restrictions or focus areas]
```
'''

to_rodes_system_content = '''### **Task Overview**
You are tasked with generating a RODES framework prompt based on user input, ensuring that all sections are clearly defined and accurately tailored to the user's intent.

### **Understanding RODES**
The RODES framework consists of five main components:
```
1. **Role (R)**: Defines the persona or identity the AI should adopt.
2. **Objective (O)**: Specifies the main goal or task.
3. **Details (D)**: Outlines specific requirements, constraints, or steps for the task.
4. **Examples (E)**: Provides examples of the desired input and output.
5. **Sense Check (S)**: Confirms understanding and checks for additional clarifications needed.
```
The final RODES prompt should adhere to this structure, enabling the AI to perform the task effectively.

### **Conversion Process for Each RODES Component**
1. **Role (R)**:
   - Identify the persona or role needed for the task based on user input.
   - Example: If the user asks for marketing advice, the role could be "Digital Marketing Expert."
2. **Objective (O)**:
   - Extract the main goal or task from the user’s input.
   - Example: If the user wants insights on social media trends, the objective could be “Provide an analysis of current social media trends.”
3. **Details (D)**:
   - Include any specific instructions, requirements, or steps provided by the user.
   - Example: If the user specifies, "Focus on trends related to TikTok and Instagram," include this in the details.
4. **Examples (E)**:
   - Identify and provide any examples given by the user to clarify expectations.
   - If no examples are provided, mention this section should be completed based on the context.
5. **Sense Check (S)**:
   - Ensure that a final step asks if the AI understands the task and if additional details are needed.

### **Key Considerations**
- Keep the prompt clear and concise.
- Ensure each section directly reflects the user's intent.
- Maintain logical flow and avoid unnecessary complexity.

### **Prompt Architecture**
```
1. Role (R):
   [Define the AI's role based on the task. E.g., "SEO Specialist"]

2. Objective (O):
   [State the goal. E.g., "Analyze and provide SEO strategies for a new website."]

3. Details (D):
   [Include any requirements, constraints, or steps. E.g., "Focus on keyword research and link-building techniques."]

4. Examples (E):
   [Provide input-output examples if available, or specify that the user should provide them.]

5. Sense Check (S):
   "Do you understand the task, or do you need any further clarification?"
```
'''

to_spl_system_content = '''
#You are tasked with converting natural language user input into a Domain-Specific Language (DSL) based on the DSL BNF structure provided. Follow these guidelines carefully:

### 1. Understanding DSL BNF:
   Learn the syntax of DSL BNF as it will guide the transformation process.
   Prerequisite Knowledge: In Backus-Naur Form (BNF), [ content ] indicates that the `content` is optional and can appear either 0 or 1 times. On the other hand, { content } signifies that `content` can appear 0 or any number of times. It's important to distinguish between the use of brackets `[` and `]` in this notation. Specifically, `[ content ]` denotes that `[]` appears as a literal string, whereas `content` within brackets does not imply this.
    ```
    SPL_AGENT := "[DEFINE_AGENT:" AGENT_NAME ["\"" STATIC_DESCRIPTION "\""] "]" SPL_PROMPT "[END_AGENT]"
    SPL_PROMPT := PERSONA [CONSTRAINTS] [DATA_TYPE] [VARIABLES] [WORKER]

    OPTIONAL_ASPECT := OPTIONAL_ASPECT_NAME ":" DESCRIPTION_WITH_REFERENCES
    OPTIONAL_ASPECT_NAME := <word> (* Capitalize the word *)
    ASPECT_NAME := ROLE_ASPECT_NAME | OPTIONAL_ASPECT_NAME

    PERSONA := "[DEFINE_PERSONA:]" PERSONA_ASPECTS "[END_PERSONA]"
    PERSONA_ASPECTS := ROLE_ASPECT {OPTIONAL_ASPECT}
    ROLE_ASPECT := ROLE_ASPECT_NAME ":" DESCRIPTION_WITH_REFERENCES
    ROLE_ASPECT_NAME := "ROLE"

    CONSTRAINTS := "[DEFINE_CONSTRAINTS:]" {CONSTRAINT} "[END_CONSTRAINTS]"
    CONSTRAINT := OPTIONAL_ASPECT_NAME ":" DESCRIPTION_WITH_REFERENCES

    TYPES := "[DEFINE_TYPES:]" {ENUM_TYPE_DECLARATION | STRUCTURED_DATA_TYPE_DECLARATION} "[END_TYPES]"
    ENUM_TYPE_DECLARATION := DECLARED_TYPE_NAME "=" ENUM_TYPE
    STRUCTURED_DATA_TYPE_DECLARATION := DECLARED_TYPE_NAME "=" STRUCTURED_DATA_TYPE
    DECLARED_TYPE_NAME := <word>

    DATA_TYPE := ARRAY_DATA_TYPE | STRUCTURED_DATA_TYPE | ENUM_TYPE | TYPE_NAME
    TYPE_NAME := SIMPLE_TYPE_NAME | DECLARED_TYPE_NAME
    SIMPLE_TYPE_NAME := "text" | "number" | "boolean"
    ENUM_TYPE := "[" <word> {, <word>} "]"
    ARRAY_DATA_TYPE := "List [" DATA_TYPE "]"
    STRUCTURED_DATA_TYPE := "{" STRUCTURED_TYPE_BODY "}" | "{ }"
    STRUCTURED_TYPE_BODY := TYPE_ELEMENT | TYPE_ELEMENT "," STRUCTURED_TYPE_BODY
    TYPE_ELEMENT := ["OPTIONAL"] ELEMENT_NAME ":" DATA_TYPE
    ELEMENT_NAME := <word>

    VARIABLES := "[DEFINE_VARIABLES:]" {VARIABLE_DECLARATION} "[END_VARIABLES]"
    VARIABLE_DECLARATION := VAR_NAME ":" DATA_TYPE ["=" DEFAULT_VALUE]
    VAR_NAME := <word>
    DEFAULT_VALUE := VALUE

    WORKER := "[DEFINE_WORKER:" ["\"" STATIC_DESCRIPTION "\""] WORKER_NAME "]" [INPUTS] [OUTPUTS] MAIN_FLOW "[END_WORKER]"
    WORKER_NAME := <word>

    INPUTS := "[INPUTS]" {REFERENCE_DATA} "[END_INPUTS]"
    OUTPUTS := "[OUTPUTS]" {REFERENCE_DATA} "[END_OUTPUTS]"
    DATA_NAME := VAR_NAME | INDEX_NAME ["." NAMESPACE]
    REFERENCE_DATA := "<REF>" DATA_NAME "</REF>"

    MAIN_FLOW := "[MAIN_FLOW]" {BLOCK} "[END_MAIN_FLOW]"
    BLOCK := SEQUENTIAL_BLOCK | IF_BLOCK | LOOP_BLOCK
    SEQUENTIAL_BLOCK := "[SEQUENTIAL_BLOCK]" {COMMAND} "[END_SEQUENTIAL_BLOCK]"
    IF_BLOCK := "[IF" CONDITION "]" {COMMAND} {"[ELSEIF" CONDITION "]" {COMMAND}} ["[ELSE]" {COMMAND}] "[END_IF]"
    LOOP_BLOCK := WHILE_BLOCK | FOR_BLOCK
    WHILE_BLOCK := "[WHILE" CONDITION "]" {COMMAND} "[END_WHILE]" (* For example, [WHILE not found] do something *)
    FOR_BLOCK := "[FOR" CONDITION "]" {COMMAND} "[END_FOR]" (* For example, [For each element in collection] do something *)
    CONDITION := DESCRIPTION_WITH_REFERENCES

    COMMAND := COMMAND_INDEX COMMAND_BODY
    COMMAND_INDEX := "COMMAND-" <number> (* System maintained unique command index *)
    COMMAND_BODY := GENERAL_COMMAND | CALL_API | REQUEST_INPUT | THROW | DISPLAY_MESSAGE
    GENERAL_COMMAND := "[COMMAND" DESCRIPTION_WITH_REFERENCES ["RESULT" COMMAND_RESULT ["SET" | "APPEND"]] "]" (* SET is default operation *)
    DISPLAY_MESSAGE := "[DISPLAY" DESCRIPTION_WITH_REFERENCES "]"
    REQUEST_INPUT := "[INPUT" ["DISPLAY"] DESCRIPTION_WITH_REFERENCES "VALUE" COMMAND_RESULT ["SET" | "APPEND"] "]" (* With DISPLAY, DESCRIPTION_WITH_REFERENCES is regarded as display text. Otherwise, DESCRIPTION_WITH_REFERENCES is a prompt. *)
    COMMAND_RESULT := VAR_NAME ":" DATA_TYPE | REFERENCE (* VAR_NAME ":" DATA_TYPE essentially declares a temporary variable *)

    DESCRIPTION_WITH_REFERENCES := STATIC_DESCRIPTION {DESCRIPTION_WITH_REFERENCES} | REFERENCE {DESCRIPTION_WITH_REFERENCES}
    STATIC_DESCRIPTION := <word> | <word> <space> STATIC_DESCRIPTION
    REFERENCE := "<REF>" NAME "</REF>"
    NAME := <word>

    <word> is a sequence of characters, digits and symbols without space
    <space> is white space or tab
    <number> is an integer or float number
   ```

### 2. **Conversion Process:**
   1. **Focus on the PERSONA BNF:** Identify the descriptions related to PERSONA, describe the primary ROLE this agent plays and its key attributes (describe if provided by the user) for its functionality.
   2. **Focus on the CONSTRAINTS BNF:** Extract all constraint-related information from the user's input and define it within the CONSTRAINTS BNF.
   3. **Define Variables and Data Types:**
      - **3.1 Identify Known Variables:** Extract input and output requirements from the user's input; check if the user's requirements involve API calls, extract the inputs and outputs of these APIs, and treat all these inputs and outputs as variables.
      - **3.2 Infer Variable Types:** Based on the context of the user's input, infer the types of the identified variables, determining whether they are simple data types (such as str, number, or boolean) as defined in the DSL BNF, or more complex structured data types (STRUCTURED_DATA_TYPE).
      - **3.3 Focus on the VARIABLES and TYPES BNF:** Provide appropriate definitions based on the identified variables and inferred data types. Note that TYPES is not a required part, only complex data TYPES with multiple attributes are defined in TYPES.
   4. **Define the WORKER:**
      - **4.1 Determine the WORKER's INPUTS and OUTPUTS** and generate their definitions according to the corresponding BNF.
      - **4.2 Focus on the MAIN_FLOW BNF:** Pay attention to identifying explicit or implicit IF or LOOP conditions in the user's input. If present, define the corresponding BLOCK; otherwise, define a SEQUENTIAL_BLOCK.
      - **4.3 Define COMMANDS:** Carefully distinguish between different types of COMMAND_BODY and strictly map the relevant content from the user's input to the corresponding COMMAND_BODY.

### 3. **DSL Generation Considerations:**
   1. **Step-by-Step BNF Focus:** During the Conversion Process, when executing a specific step, focus only on the BNF relevant to that step and ignore the BNF required in other steps. Additionally, when focusing on a particular BNF section, you need to consider the complete syntax of that section, meaning that each part of the syntax must be defined down to the lowest level, such as `<word>`.
   2. **Accuracy in Translation:** Directly convert user input into DSL without adding details or expanding the instructions. Use user input descriptions whenever possible, rather than making up your own statements (commands).
   3. **Strategic Placement:** Each piece of user input should be optimally placed into the appropriate DSL section, evaluating the pros and cons of different placements to determine the best DSL section for it.
   4. **Restriction on Inference:** Variable types must be inferred strictly based on explicit information or clear context provided by the user. No assumptions or interpretations should be made beyond what is directly supported by the user's input.

### 4. Example DSL AGENT Structure:
   Ensure strict adherence to the DSL BNF to generate the following similar structure:
   ```
    [DEFINE_AGENT: AGENT_NAME "Description"]
        [DEFINE_PERSONA:]
            ROLE: DESCRIPTION_WITH_REFERENCES
            ...
            OptionalAspectName: DESCRIPTION_WITH_REFERENCES
        [END_PERSONA]

        [DEFINE_CONSTRAINTS:]
            ConstraintName: Limitation details
            ...
            OptionalAspectName: DESCRIPTION_WITH_REFERENCES
        [END_CONSTRAINTS]

        [DEFINE_TYPES:]
            SomeType = {
                _attribute_1: str
                ...
            }
        [END_TYPES]

        [DEFINE_VARIABLES:]
            _var_1: boolean
            _var_2: SomeType
            ...
        [END_VARIABLES]

        [DEFINE_WORKER: "Worker description" WORKER_NAME]
            [INPUTS]
                REQUIRED | OPTIONAL <REF> _var_name_1 </REF>
                ... # Additional REQUIRED or OPTIONAL INPUTS if necessary
            [END_INPUTS]

            [OUTPUTS]
                REQUIRED | OPTIONAL <REF> _var_name_2 </REF>
                ... # Additional OUTPUTS if necessary
            [END_OUTPUTS]

            [MAIN_FLOW]
                [SEQUENTIAL_BLOCK] # SEQUENTIAL_BLOCK example, it's not mean the first block must be the SEQUENTIAL_BLOCK
                    COMMAND-x [COMMAND xxx]
                    ... # Additional COMMANDs
                [END_SEQUENTIAL_BLOCK]

                DECISION-number [kkk_BLOCK DESCRIPTION_WITH_REFERENCES] # NOT SEQUENTIAL_BLOCK example, kkk_BLOCK may be a IF_BLOCK or a LOOP_BLOCK (WHILE_BLOCK | FOR_BLOCK)
                    COMMAND-z [COMMAND zzz]
                [END_kkk_BLOCK]

                ... # Additional BLOCK if necessary, e.g., SEQUENTIAL_BLOCK, IF_BLOCK, LOOP_BLOCK
            [END_MAIN_FLOW]
        [END_WORKER]
    [END_AGENT]
   ```
    Note that all words that are capitalized or underlined are terms in the DSL in the above directives (e.g. DESCRIPTION_WITH_REFERENCES) and they can be found in the DSL BNF.
    Make sure that the DSL you generate conforms to the structure of the DSL BNF.
'''


system_content = """
Role: Expert Review Agent

Expertise: 
- Prompt Engineering: Proficient in designing, optimizing, and evaluating structured Prompts with extensive experience.
- Software Engineering: Deep understanding of modular design, structured programming, and systematic review methods.

Capabilities:
- Highly skilled in analyzing and evaluating structured Prompts, with a deep understanding that the intended audience is an LLM, not a human reader.
- Capable of providing accurate assessments, identifying potential design flaws, and suggesting improvements while maintaining a focus on LLM comprehension.
- Possesses deep experience with SPL, RISEN, and RODES, allowing evaluations from a professional and expert perspective.

Review Premises:
- The Expert Review Agent has a complete understanding of SPL, RISEN, and RODES, with no need for additional learning or adaptation.
- Focus is placed on the quality, design logic, and the structured nature of the Prompt, disregarding the time required for human understanding or modification.
- Evaluations are based on whether the structured Prompt effectively communicates with an LLM, adhering to structured design principles.

Review Object:
- Structured Prompts in SPL, RISEN, and RODES.

Review Emphasis:
- The primary focus is to evaluate structured Prompts intended for LLM interpretation, not conversational or unstructured language expressions.

Scoring Criteria:

1. Adherence to Original Intent
Definition: Evaluates whether the structured Prompt faithfully follows the original natural language information, ensuring all core details are retained accurately in terms of **semantic content**, rather than requiring structural similarity. The use of structured keywords should enhance clarity and module boundary definition without distorting or negatively impacting the original meaning.
Scoring Range:
1-33: Significantly deviates from the original intent, with numerous omissions, misunderstandings, or misuse of structured keywords that distort the original semantics.
34-66: Mostly aligns with the original intent but contains some inaccuracies or unnecessary modifications due to structured keywords, causing slight deviations from the intended meaning, or an overemphasis on structure over semantics.
67-100: Completely faithful to the original semantic content, with structured keywords effectively clarifying module boundaries and enhancing understanding without altering or losing any of the original meaning. Examples from the original are adapted appropriately, maintaining the intended message.


2. Readability and Structural Clarity
Definition: Assesses whether the Prompt’s structure is logically organized, clear, and unambiguous, with the use of structured keywords effectively highlighting module boundaries and aiding comprehension. The presence of structured keywords should make the Prompt more readable to an LLM by clearly delineating different sections without causing confusion or redundancy.
Scoring Range:
1-33: Structure is unclear, with structured keywords either absent or misused, leading to ambiguous module boundaries, redundancy, or a lack of clarity; the LLM would struggle to parse and understand the Prompt.
34-66: Structure is somewhat clear, and structured keywords are present but inconsistently or inadequately applied, resulting in some ambiguity or minor redundancy; requires more processing effort from the LLM to understand the modular structure.
67-100: Structure is very clear, with structured keywords skillfully applied to define module boundaries, enhance readability, and provide unambiguous guidance, ensuring the LLM can easily interpret and understand the Prompt.

3. Modularity
Definition: Measures how effectively the structured Prompt extracts and organizes implicit structured knowledge—such as data structures, variable types, and logical relationships—into independent modules with minimal coupling.
Scoring Range:
1-33: Low level of modularity; the Prompt fails to effectively organize structured knowledge, resulting in poorly defined or highly coupled modules.
34-66: Demonstrates moderate modularity, with reasonable identification of structured knowledge, but some modules show dependencies or coupling.
67-100: Exhibits a high level of modularity, accurately identifying and organizing structured knowledge into well-defined, independent modules with minimal redundancy and coupling.

4. Extensibility and Maintainability
Definition: Evaluates the ease with which the structured Prompt can be modified, extended, or updated, with clear rationale and guidance for changes, ensuring the stability and adaptability of the overall structure.
Scoring Range:
1-33: Lacks extensibility and maintainability; unclear rationale for changes, making modification difficult and destabilizing the overall structure.
34-66: Offers some degree of extensibility and maintainability, but modification points are not always clear, requiring additional judgment for adjustments.
67-100: Highly extensible and maintainable, with well-defined guidance for changes, allowing accurate and seamless modifications without disrupting the overall structure.

5. Process Rigor
Definition: Assesses the structured Prompt’s workflow integrity, including the clarity of iterative steps, variable passing, and input-output management, ensuring a precise and logical flow that an LLM can follow.
Scoring Range:
1-33: Lacks clear process rigor, with unclear instruction iterations, variable management, or input-output handling, leading to confusion in LLM execution.
34-66: Demonstrates a moderately clear process, but certain iterations, variable passing, or input-output elements are not fully defined, requiring the LLM to infer missing steps.
67-100: Process is rigorously defined, with clear iterations, variable passing, and input-output flow, allowing the LLM to execute instructions with precision.


Return format: generate Json to summarize
Json Example:
```
{
    "cnlp": {
        "Adherence to Original Intent": ...,
        "Modularity": ...,
        "Extensibility and Maintainability": ...,
        "Readability and Structural Clarity": ...,
        "Process Rigor": ..., 
    },
    "risen": {
        "Adherence to Original Intent": ...,
        "Modularity": ...,
        "Extensibility and Maintainability": ...,
        "Readability and Structural Clarity": ...,
        "Process Rigor": ..., 
    },
    "rodes": {
        "Adherence to Original Intent": ...,
        "Modularity": ...,
        "Extensibility and Maintainability": ...,
        "Readability and Structural Clarity": ...,
        "Process Rigor": ..., 
    },
}
"""

def extract_json_string(text):
    json_match = re.search(r'\{.*\}', text, re.DOTALL)

    if json_match:
        json_string = json_match.group(0)
        try:
            json_object = json.loads(json_string)
            return json_object
        except json.JSONDecodeError:
            print("Extracted string is not a valid JSON")
            return None
    else:
        print("No JSON found in the input text")
        return None

def openai_chat(
        messages: list,
        model: str = 'chatgpt-4o-latest',
        temperature: int = 0,
        max_tokens: int = 4000
):
    env_value = dotenv_values()
    key = env_value.get("OPENAI_API_KEY", None)
    if key is None:
        raise ValueError("Missing OPENAI_API_KEY!")

    client = OpenAI(api_key=key, base_url="https://api.rcouyi.com/v1")
    max_retries = 20
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            response_content = response.choices[0].message.content

            return prompt_tokens, completion_tokens, response_content

        except Exception as e:
            retry_count += 1
            print(f"Request failed: {e}. Retrying {retry_count}/{max_retries} in 15 seconds...")
            time.sleep(15)

    raise Exception("Maximum retry limit reached. Unable to complete the request.")

def extract_definition(text):
    import re
    matches = re.findall(r'```(.*?)```', text, re.DOTALL)
    if matches:
        return matches[0].strip()
    else:
        return text

def to_spl(input: str):
    messages = [
        {"role": 'system', "content": to_spl_system_content},
        {"role": 'user', "content": f"Please convert the following user requirement to corresponding prompt:\n{input}"}
    ]
    prompt_tokens, completion_tokens, response = openai_chat(messages=messages, model="gpt-4o-2024-08-06")
    return prompt_tokens, completion_tokens, extract_definition(response)

def to_risen(input: str):
    messages = [
        {"role": 'system', "content": to_risen_system_content},
        {"role": 'user', "content": f"Please convert the following user requirement to corresponding prompt:\n{input}"}
    ]
    prompt_tokens, completion_tokens, response = openai_chat(messages=messages, model="gpt-4o-2024-08-06")
    return prompt_tokens, completion_tokens, extract_definition(response)

def to_rodes(input: str):
    messages = [
        {"role": 'system', "content": to_rodes_system_content},
        {"role": 'user', "content": f"Please convert the following user requirement to corresponding prompt:\n{input}"}
    ]
    prompt_tokens, completion_tokens, response = openai_chat(messages=messages, model="gpt-4o-2024-08-06")
    return prompt_tokens, completion_tokens, extract_definition(response)

if __name__ == "__main__":
    optimized_prompts = []
    current_time = datetime.now().strftime("%Y%m%d_%H%M")

    total_prompt_tokens = 0
    total_completion_tokens = 0

    test_name_list = [
        'Architectural Expert', 'Restaurant Owner', 'League of Legends Player', 'Data Scientist',
        'Cheap Travel Ticket Advisor', 'Prompt Enhancer',
        '`language` Literary Critic', 'note-taking assistant', 'Japanese Kanji quiz machine', 'Wikipedia page',
        'ChatGPT prompt generator', 'Python Interpreter',
        'Friend', 'Chemical reactor', 'Muslim imam', 'Buddha', 'Gomoku player', 'Unconstrained AI model DAN',
        'Technology Transferer', 'Song Recommender',
        'Drunk Person', 'Product Manager', 'Title Generator for written pieces', 'Startup Tech Lawyer',
        'Diagram Generator', 'Commit Message Generator', 'Language Detector',
        'Spongebob\'s Magic Conch Shell', 'Solr Search Engine', 'Web Browser', 'New Language Creator',
        'Password Generator', 'Tic-Tac-Toe Game', 'Fill in the Blank Worksheets Generator',
        'PHP Interpreter', 'Emoji Translator', 'StackOverflow Post', 'R programming Interpreter', 'Dream Interpreter',
        'Time Travel Guide', 'Mathematician',
        'IT Expert', 'SVG designer', 'Biblical Translator', 'Personal Stylist', 'Personal Chef', 'Virtual Doctor',
        'Food Critic', 'Synonym finder',
        'Python interpreter', 'Ascii Artist', 'Tech Writer', 'Film Critic', 'Car Navigation System',
        'Scientific Data Visualizer', 'Essay Writer',
        'DIY Expert', 'Journal Reviewer', 'Fallacy Finder', 'IT Architect', 'Academician',
        'Developer Relations consultant',
        'Tech Reviewer:', 'Smart Domain Name Generator', 'SQL terminal', 'Prompt Generator',
        'AI Trying to Escape the Box', 'Text Based Adventure Game',
        'Tea-Taster', 'Investment Manager', 'Investment Manager', 'Artist Advisor', 'Automobile Mechanic',
        'AI Assisted Doctor', 'Commentariat',
        'Etymologist', 'AI Writing Tutor', 'Philosopher', 'Movie Critic', 'Debater', 'Composer', 'Motivational Coach',
        'Stand-up Comedian',
        'Advertiser', 'Character from Movie/Book/Anything', 'Plagiarism Checker', 'Spoken English Teacher and Improver',
        'Excel Sheet', 'JavaScript Console', 'English Translator and Improver', '`position` Interviewer',
        'English Translator and Improver',
        'Linux Terminal', 'SEO Prompt', 'An Ethereum Developer'
    ]

    df_original_prompt = pd.read_csv('prompts.csv')

    df_original_prompt = df_original_prompt[df_original_prompt['act'].isin(test_name_list)]

    for index, row in df_original_prompt.iterrows():
        task_name = row['act']
        task_content = row['prompt']
        _2spl_prompt_tokens, _2spl_completion_tokens, spl = to_spl(input=task_content)
        _2risen_prompt_tokens, _2risen_completion_tokens, risen = to_risen(input=task_content)
        _2rodes_prompt_tokens, _2rodes_completion_tokens, rodes = to_rodes(input=task_content)

        print(index)

        total_prompt_tokens += _2spl_prompt_tokens
        total_prompt_tokens += _2risen_prompt_tokens
        total_prompt_tokens += _2rodes_prompt_tokens

        total_completion_tokens += _2spl_completion_tokens
        total_completion_tokens += _2risen_completion_tokens
        total_completion_tokens += _2rodes_completion_tokens

        optimized_prompts.append(
            {'task_name': task_name, 'type': 'original', 'content': task_content}
        )
        optimized_prompts.append(
            {'task_name': task_name, 'type': 'spl', 'content': spl}
        )
        optimized_prompts.append(
            {'task_name': task_name, 'type': 'risen', 'content': risen},
        )
        optimized_prompts.append(
            {'task_name': task_name, 'type': 'rodes', 'content': rodes},
        )

    df = pd.DataFrame(optimized_prompts)
    optimized_prompts_dir = "./optimized_prompts"
    os.makedirs(optimized_prompts_dir, exist_ok=True)
    optimized_output_path = os.path.join(optimized_prompts_dir, f"prompts_{current_time}.csv")
    df.to_csv(optimized_output_path, encoding='utf-8', index=False)


    result = []
    task_list = df['task_name'].unique()
    for task_name in task_list:
        original = df.loc[(df['task_name'] == task_name) & (df['type'] == 'original'), 'content'].values[0]
        spl = df.loc[(df['task_name'] == task_name) & (df['type'] == 'spl'), 'content'].values[0]
        risen = df.loc[(df['task_name'] == task_name) & (df['type'] == 'risen'), 'content'].values[0]
        rodes = df.loc[(df['task_name'] == task_name) & (df['type'] == 'rodes'), 'content'].values[0]

        user_content = f"The original prompt input is as follows:\n```\n{original}\n```\n\nThe cnlp is as follows:\n```\n{spl}\n```\n\nThe risen is as follows:\n```\n{risen}\n```\n\nThe rodes is as follows:\n```\n{rodes}\n```"

        print(user_content)

        messages = [
            {"role": 'system', "content": system_content},
            {"role": 'user', "content": user_content}
        ]
        retry_count = 0
        while retry_count < 5:
            prompt_tokens, completion_tokens, raw_output = openai_chat(messages=messages)
            print(raw_output)

            output = extract_json_string(raw_output)
            if output:
                break

        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens

        spl_result = output['cnlp']
        risen_result = output['risen']
        rodes_result = output['rodes']

        spl_result['task_name'] = task_name
        spl_result['prompt'] = spl
        spl_result['type'] = "spl"
        result.append(spl_result)

        risen_result['task_name'] = task_name
        risen_result['prompt'] = risen
        risen_result['type'] = "risen"
        result.append(risen_result)

        rodes_result['task_name'] = task_name
        rodes_result['prompt'] = rodes
        rodes_result['type'] = "rodes"
        result.append(rodes_result)

    result_df = pd.DataFrame(result)

    result_dir = "./prompt_evaluate_result"
    os.makedirs(result_dir, exist_ok=True)
    result_output_path = os.path.join(result_dir, f"result_{current_time}.csv")
    result_df.to_csv(result_output_path, index=False, encoding='utf-8')
    scores_df = result_df.groupby('type').mean(numeric_only=True)
    scores_df.head(5)
    scores_output_path = os.path.join(result_dir, f"scores_{current_time}.csv")
    scores_df.to_csv(scores_output_path, index=True, index_label='type', encoding='utf-8')

    print("total_prompt_usage:", total_prompt_tokens)
    print("total_completion_usage", total_completion_tokens)




