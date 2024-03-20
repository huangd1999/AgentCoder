from datasets import load_dataset

dataset = load_dataset("THUDM/humaneval-x",name="cpp",split="test")
for key in dataset[0].keys():
    print("===================")
    print("key:",key)
    print(dataset[1][key])

dataset = [example for example in dataset]

