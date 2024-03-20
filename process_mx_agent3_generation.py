import json
def preprocess_data(data,lg):
    if f"```{lg}" in data["completion"]:
        data["completion"] = data["completion"][data["completion"].find(f"```{lg}")+len(f"```{lg}"):]
        data["completion"] = data["completion"][:data["completion"].find("```")]
    else:
        print(data["task_id"])
        # data["completion"] = "Raise NotImplementedError"
    return data
if __name__ == "__main__":
    model_list = ["gpt-3.5-turbo"]
    language = ["python", "java","go","php","ruby","scala"]
    language = ["python"]
    for model in model_list:
        for lg in language:
            with open(f"./dataset/{model}_{lg}.json", "r") as f:
                dataset = json.load(f)

            for i in range(len(dataset)):
                dataset[i] = preprocess_data(dataset[i],lg)
            with open(f"./dataset/{model}_{lg}.json", "w") as f:
                json.dump(dataset, f, indent=4)
