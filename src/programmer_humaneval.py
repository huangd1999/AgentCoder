# Improve readability of the code by Claude-3-opus:

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
openai.api_key = 'sk-e8d20ad67ba241228469ae8c37877f41'

dataset = load_dataset("openai_humaneval", split="test")
dataset = [entry for entry in dataset]

prompt_path = "../prompts/humaneval_prompt_update.txt"
with open(prompt_path, "r") as f:
    construct_few_shot_prompt = f.read()


def preprocess_data(completion_string):
    if "```python" in completion_string:
        start_index = completion_string.find("```python") + len("```python")
        end_index = completion_string.find("```", start_index)
        completion_string = completion_string[start_index:end_index]
    else:
        print("Error: No code block found")
    return completion_string


def fetch_completion(data_entry, model, lg):
    global construct_few_shot_prompt
    prompt = data_entry["prompt"]
    text = f"""
{construct_few_shot_prompt}
**Input Code Snippet**:
```{lg}
{prompt}
```
"""
    try:
        completions = openai.ChatCompletion.create(
            model=model,
            stream=False,
            messages=[
                {"role": "system", "content": "You are a software programmer."},
                {"role": "user", "content": text},
            ],
            request_timeout=100,
        )
        completion = completions.choices[0]["message"]["content"]
        data_entry["completion"] = preprocess_data(completion)
    except Exception as e:
        print(e)
        time.sleep(10)
        completion = "API Error"
    return data_entry


def fix_bug(data_entry, model, lg, preprocess_data=preprocess_data):
    if f"assert {data_entry['entry_point']}" not in data_entry["incorrect_tests"]:
        return data_entry
    else:
        gpt_prompt = (f"""
Please re-completion the code to fix the error message.
Here is the previous version:
```{lg}\n{data_entry['completion']}\n```
When we use this test cases: 
```{lg}\n{data_entry["incorrect_tests"]}\n``` 
to evaluate the code. It raise the error:
```{lg}\n{data_entry["result"]}]\n```
Please fix the bug by follow the error information and only return {lg} code. You do not need return the test cases.
The re-completion code should in triple backticks format(i.e., in ```{lg} ```)."
"""
        )
        try:
            completions = openai.ChatCompletion.create(
                model=model,
                stream=False,
                messages=[
                    {"role": "system", "content": "You are a code developer assistant."},
                    {"role": "user", "content": gpt_prompt},
                ],
                request_timeout=100,
            )
            data_entry["completion"] = completions.choices[0]["message"]["content"]
            data_entry = preprocess_data(data_entry, lg)
        except Exception as e:
            print(repr(e))
    return data_entry


def call_fix_bug(dataset, model, lg):
    print("Fixing bug...")
    with ThreadPoolExecutor() as executor:
        future_to_entry = {executor.submit(fix_bug, copy.deepcopy(entry), model, lg): entry for entry in tqdm(dataset)}
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
    model_list = ["gpt-3.5-turbo"]
    language = ["python"]
    for model in model_list:
        for lg in language:
            dataset = load_dataset("openai_humaneval", split="test")
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
            with open(f"../dataset/humaneval_{model}_{lg}.json", "w") as f:
                json.dump(dataset, f, indent=4)
