import argparse
import os
import json
from tqdm import tqdm
import copy
import openai
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
from datasets import load_dataset
# Setting API parameters
openai.api_base = "https://api.aiohub.org/v1"
openai.api_key = 'YOUR API KEY'

dataset = load_dataset("openai_humaneval",split="test")
dataset = [entry for entry in dataset]


task_0_tests = """
assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False
assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)== True
"""

task_1_tests = """
assert separate_paren_groups('( ) (( )) (( )( ))') == ['()', '(())', '(()())']
"""
construct_few_shot_prompt = f"""
# For example:

## Prompt 1:
```python
{dataset[0]["prompt"]}
```

## Completion 1:
```python
{task_0_tests}
```

## Prompt 2:
```python
{dataset[1]["prompt"]}
```

## Completion 2:
```python
{task_1_tests}
```
"""

def preprocess_data(test_case_string):
    if f"```python" in test_case_string:
        test_case_string = test_case_string[test_case_string.find(f"```python")+len(f"```python"):]
        test_case_string = test_case_string[:test_case_string.find("```")]
    else:
        print("Error: No code block found")
    return test_case_string

# Function to fetch completion
def fetch_completion(data_entry, model, lg,times=5):
    global construct_few_shot_prompt
    if "need_reproduce" in data_entry.keys() and data_entry["need_reproduce"]==False:
        return data_entry
    prompt = data_entry["prompt"]
    entry_point = data_entry["entry_point"]
    
    text = f"""
**Role**: As a tester, your task is to create comprehensive test cases for the incomplete `{entry_point}` function.

- The format of test cases should be:
```python
assert function_name(input) == expected_output, "Test Case Description"
```

{construct_few_shot_prompt}

**Input Code Snippet**:
```python
{prompt}
```
"""
    test_case_list = []
    for i in range(times):
        while True:
            try:
                completions = openai.ChatCompletion.create(
                    model=model,
                    stream=False,
                    messages=[
                {"role": "system", "content": "You are a code developer assistant."},
                {"role": "user", "content":text},
                    ],
                    request_timeout=100,
                )
                test_case = completions.choices[0]["message"]["content"]
                test_case = preprocess_data(test_case)
            except Exception as e:
                time.sleep(20)
                print(e)
                test_case = ""
            if test_case!="":
                break
        test_case_list.append(test_case)
    data_entry["test_case_list"] = test_case_list
    return data_entry

def call_fetch_test_completion_helper(dataset, model,lg):
    print("Fixing bug...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg): entry for entry in tqdm(dataset)}
        for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                print(repr(e))
    return dataset


if __name__ == "__main__":

    model_list = ["gpt-3.5-turbo-1106"]
    language = ["python"]
    for model in model_list:
        for lg in language:
            from datasets import load_dataset
            # dataset = load_dataset("openai_humaneval",split="test")
            with open(f"./dataset/{model}_{lg}.json", "r") as f:
                dataset = json.load(f)
            dataset = [entry for entry in dataset]
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg): entry for entry in tqdm(dataset)}
                for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
                    entry = future_to_entry[future]
                    try:
                        updated_entry = future.result()
                        idx = dataset.index(entry)
                        dataset[idx] = updated_entry
                    except Exception as e:
                        print(repr(e))

            with open(f"./dataset/{model}_{lg}.json", "w") as f:
                json.dump(dataset, f, indent=4)
