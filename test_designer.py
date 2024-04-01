import argparse
import os
import json
from tqdm import tqdm
import copy
import openai
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

# Setting API parameters
openai.api_base = "https://api.aiohub.org/v1"
openai.api_key = 'API'


def preprocess_data(data,lg):
    if f"```{lg}" in data["test_case"]:
        data["test_case"] = data["test_case"][data["test_case"].find(f"```{lg}")+len(f"```{lg}"):]
        data["test_case"] = data["test_case"][:data["test_case"].find("```")]
    else:
        print(data["task_id"])
    return data

# Function to fetch completion
def fetch_completion(data_entry, model, lg):
    prompt = data_entry["prompt"]
    completion = data_entry["completion"]
    entry_point = data_entry["entry_point"]
    
    text = f"""
**Role**: As a tester, your task is to create comprehensive test cases for the incomplete `{entry_point}` function. These test cases should encompass Basic, Edge, and Large Scale scenarios to ensure the code's robustness, reliability, and scalability.

**Input Code Snippet**:
```python
{prompt}
### Please decided how would you want to generate test cases. Based on incomplete code or completed version.
{completion}
```
**1. Basic Test Cases**:
- **Objective**: To verify the fundamental functionality of the `has_close_elements` function under normal conditions.

**2. Edge Test Cases**:
- **Objective**: To evaluate the function's behavior under extreme or unusual conditions.

**3. Large Scale Test Cases**:
- **Objective**: To assess the function’s performance and scalability with large data samples.

**Instructions**:
- Implement a comprehensive set of test cases following the guidelines above.
- Ensure each test case is well-documented with comments explaining the scenario it covers.
- Pay special attention to edge cases as they often reveal hidden bugs.
- For large-scale tests, focus on the function's efficiency and performance under heavy loads.
"""
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
        data_entry["test_case"] = completions.choices[0]["message"]["content"]
        data_entry = preprocess_data(data_entry,lg)
        return data_entry
    except Exception:
        data_entry["test_case"] = ""
        return data_entry



# Loading the dataset
# model_list = ["gpt-3.5-turbo","gpt-3.5-turbo-0301","palm-2-codechat-bison","claude-instant-1"]

model_list = ["gpt-3.5-turbo"]
# language = ["python", "java","go","php","ruby","scala"]
language = ["python"]
for model in model_list:
    for lg in language:
        from datasets import load_dataset
        # dataset = load_dataset("openai_humaneval",split="test")
        with open(f"./dataset/{model}_{lg}.json", "r") as f:
            dataset = json.load(f)
        dataset = [entry for entry in dataset]
        with ThreadPoolExecutor() as executor:
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
