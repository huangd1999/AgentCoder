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
openai.api_key = 'API key'





# Function to fetch completion
def fetch_completion(data_entry, model,lg):
    text = f"""
Please follow the example's format to completion function.
the generated test cases should one rule:
The output must in triple backticks format script.
Below is a example:
### Input:
```python
from typing import List 
def has_close_elements(numbers: List[float], threshold: float) -> bool: 
    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than given threshold. 
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5) False 
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) True 
    \"\"\"
```

### Response:
```python
has_close_elements
```
"""
    try:
        completions = openai.ChatCompletion.create(
            model=model,
            stream=False,
            messages=[
        {"role": "system", "content": "You are a code developer assistant."},
        {"role": "user", "content":text+f"\n### Input:\n```{lg}"+data_entry["prompt"]+f"\n```"},
            ],
            request_timeout=100,
        )
        data_entry["entry_point"] = completions.choices[0]["message"]["content"]
        return data_entry
    except Exception:
        try:
            completions = openai.ChatCompletion.create(
                model=model,
                stream=False,
                messages=[
        {"role": "system", "content": "You are a code developer assistant."},
        {"role": "user", "content":text+f"\n### Input:\n```{lg}"+data_entry["prompt"]+f"\n```"},
            ],
                request_timeout=100,
            )
            data_entry["entry_point"] = completions.choices[0]["message"]["content"]
            return data_entry
        except Exception as e:
            print(repr(e))
            data_entry["entry_point"] = ""
            return data_entry




model_list = ["gpt-3.5-turbo"]
# language = ["python","java","go","php","ruby","scala"]
language = ["go","cpp","java","js","python"]
for model in model_list:
    for lg in language:
        from datasets import load_dataset
        dataset = load_dataset("THUDM/humaneval-x",name=f"{lg}",split="test")
        # with open("./HumanEval.jsonl", "r") as f:
        #     dataset = [json.loads(line) for line in f.readlines()]
        # with open(f"./agent1/{model}_{lg}_backup.json", "r") as f:
        #     dataset = json.load(f)
        dataset = [entry for entry in dataset]
        with ThreadPoolExecutor(max_workers=10) as executor:
        # with ThreadPoolExecutor() as executor:
            future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg): entry for entry in tqdm(dataset)}
            for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
                entry = future_to_entry[future]
                try:
                    updated_entry = future.result()
                    idx = dataset.index(entry)
                    dataset[idx] = updated_entry
                except Exception as e:
                    print(repr(e))

        with open(f"./agent1/{model}_{lg}.json", "w") as f:
            json.dump(dataset, f, indent=4)
