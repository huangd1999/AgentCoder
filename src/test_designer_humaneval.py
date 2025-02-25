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

dataset = load_dataset("openai_humaneval",split="test")
dataset = [entry for entry in dataset]

prompt_path = "../prompts/test_designer_humaneval_prompt_update.txt"
with open(prompt_path, "r") as f:
    construct_few_shot_prompt = f.read()

def preprocess_data(test_case_string):
    if f"```python" in test_case_string:
        test_case_string = test_case_string[test_case_string.find(f"```python")+len(f"```python"):]
        test_case_string = test_case_string[:test_case_string.find("```")]

    return test_case_string

# Function to fetch completion
def fetch_completion(data_entry, model, lg,times=10):
    global construct_few_shot_prompt
    prompt = data_entry["prompt"]
    entry_point = data_entry["entry_point"]
    
    text = f"""
{construct_few_shot_prompt}
**Input Code Snippet**:
```python
{prompt}
```
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
        test_case = completions.choices[0]["message"]["content"]
        data_entry["test_case"] = preprocess_data(test_case)
    except Exception as e:
        time.sleep(20)
        print(e)
        data_entry["test_case"] = "API Error"
    return data_entry



if __name__ == "__main__":
    model_list = ["gpt-3.5-turbo"]
    language = ["python"]
    for model in model_list:
        for lg in language:
            with open(f"../dataset/humaneval_{model}_{lg}.json", "r") as f:
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

            with open(f"../dataset/humaneval_{model}_{lg}.json", "w") as f:
                json.dump(dataset, f, indent=4)
