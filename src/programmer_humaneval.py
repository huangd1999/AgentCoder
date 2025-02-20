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
from dotenv import load_dotenv

load_dotenv()

# Setting API parameters
openai.api_base = "https://api.aiohub.org/v1"
openai.api_key = os.getenv("OPENAI_API_KEY")

dataset = load_dataset("openai_humaneval",split="test")
dataset = [entry for entry in dataset]

prompt_path = "./prompts/humaneval_prompt_update.txt"
with open(prompt_path, "r") as f:
    construct_few_shot_prompt = f.read()

def preprocess_data(completion_string):
    if f"```python" in completion_string:
        completion_string = completion_string[completion_string.find(f"```python")+len(f"```python"):]
        completion_string = completion_string[:completion_string.find("```")]
    else:
        print("Error: No code block found")
    return completion_string

# Function to fetch completion
def fetch_completion(data_entry, model,lg,times = 5):
    global construct_few_shot_prompt
    if "need_reproduce" in data_entry.keys() and data_entry["need_reproduce"]==False:
        return data_entry
    prompt = data_entry["prompt"]
    text = f"""
{construct_few_shot_prompt}

**Input Code Snippet**:
```python
{prompt}
```
## Completion 3:
"""
    completions_code = []
    for i in range(times):
        while True:
            try:
                completions = openai.ChatCompletion.create(
                    model=model,
                    stream=False,
                    messages=[
                {"role": "system", "content": "You are a software programmer."},
                {"role": "user", "content":text},
                    ],
                    request_timeout=100,
                )
                completion = completions.choices[0]["message"]["content"]
                completion = preprocess_data(completion)

            except Exception as e:
                print(e)
                time.sleep(10)
                completion = ""
            if completion!="":
                break
        completions_code.append(completion)
    data_entry["completion_list"] = completions_code
    return data_entry


def call_fetch_completion_helper(dataset, model,lg):
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
            dataset = load_dataset("openai_humaneval",split="test")
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
