# test
import random
import json
from typing import Optional, Callable, Dict
import ast
import doctest
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
import numpy as np
import sys
sys.path.append('../CodeGeeX/')
import contextlib
import io
import signal
import concurrent.futures
from tqdm import tqdm
from tqdm import tqdm
from programmer_humaneval import call_fix_bug
from codegeex.benchmark.utils import IMPORT_HELPER
from codegeex.benchmark.execution import check_correctness
import tempfile

language = ["python","cpp","js","go","js"]


class TimeoutException(Exception):
    pass
class WriteOnlyStringIO(io.StringIO):
    """ StringIO that throws an exception when it's read from """

    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        """ Returns True if the IO object can be read. """
        return False
class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = 'stdin'

@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield

@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

def process_humaneval_test(sample, problems, example_test=False,language=language, test_case=True):
    task_id = sample["task_id"]
    task_id = problems.index(sample)
    prompt = sample["prompt"]
    if example_test and "example_test" in problems[task_id] and problems[task_id]["example_test"] != "":
        test = problems[task_id]["example_test"]
    else:
        test = problems[task_id]["test"]
    if test_case:
        test = problems[task_id]["test_case"]
    code = sample["completion"]
    # Pre-process for different languages
    if language == "python":
        code_ = []
        test_setup = "\n".join(IMPORT_HELPER["python"]) + "\n"
        if f"class sample['entry_point']" in code:
            test_string = test_setup + code + "\n" + test + "\n" + f"check({sample['entry_point']})"
        else:
            test_string = test_setup + prompt + code + "\n" + test + "\n" + f"check({sample['entry_point']})"
    elif language == "cpp":
        test_set_up = ""
        for s in IMPORT_HELPER["cpp"]:
            if s not in prompt:
                test_set_up += s + "\n"
        # test_string = test_set_up + "\n" + prompt + code + "\n" + test
        test_string = test_set_up + "\n" + code + "\n" + test
    elif language == "java":
        # if sample["declaration"] in code:
        if "class Solution" in code:
            test_string = code + "\n" + test
        else:
            test_string = prompt + code + "\n" + test
        # else:
        #     test_string = prompt + code + "\n" + test
    elif language == "js" or language == "javascript":
        # test_string = prompt + code + "\n" + test
        test_string = code + "\n" + test
    elif language == "go":
        # import_string = problems[task_id]["import"]
        # prompt = prompt.replace(import_string, "")
        if example_test and "example_test" in problems[task_id]:
            test = problems[task_id]["example_test"]
        else:
            test = problems[task_id]["test"]
        candidate_import = ["math.","strings.","strconv.","sort.","time.","regexp.","fmt.","bytes.","md5.","rand."]
        test_setup = "package main\nimport (\n	\"testing\"\n	\"github.com/stretchr/testify/assert\"\n)"
        total_string = sample["declaration"] + code + "\n" + test
        other_pkgs = []
        for pkg in candidate_import:
            if pkg in total_string:
                if pkg != "md5." and pkg!="rand":
                    other_pkgs.append("    " + "\"" + pkg[:len(pkg)-1] + "\"" + "\n")
                elif pkg == "md5.":
                    other_pkgs.append("    " + "\"" + "crypto/md5" + "\"" + "\n")
                elif pkg == "rand.":
                    other_pkgs.append("    " + "\"" + "math/rand" + "\"" + "\n")
        if other_pkgs:
            import_other_pkgs = "import (\n" + "    ".join([p + "\n" for p in other_pkgs]) + ")"
            # test_string = test_setup + "\n" + import_other_pkgs + "\n" + prompt + code + "\n" + test
            test_string = test_setup + "\n" + import_other_pkgs + "\n" + code + "\n" + test
        else:
            # test_string = test_setup + "\n" + prompt + code + "\n" + test
            test_string = test_setup + "\n" + code + "\n" + test
    elif language == "rust":
        main = "\nfn main(){ \n } \n"
        declaration = problems[task_id]["declaration"]
        test_string = main + declaration + prompt + code + test
    # print(test_string)
    return test_string



def preprocess_data(task,lg):
    if f"```{lg}" in task["completion"]:
        task["completion"] = task["completion"][task["completion"].find(f"```{lg}") +len(f"```{lg}"):]
        task["completion"] = task["completion"][:task["completion"].find("```")]
    elif "```" in task["completion"]:
        task["completion"] = task["completion"][task["completion"].find("```") +3:]
        task["completion"] = task["completion"][:task["completion"].find("```")]

    if f"```{lg}" in task["prompt"]:
        task["prompt"] = task["prompt"][task["prompt"].find(f"```{lg}") +len(f"```{lg}"):]
        task["prompt"] = task["prompt"][:task["prompt"].find("```")]
    elif "```" in task["prompt"]:
        task["prompt"] = task["prompt"][task["prompt"].find("```") +3:]
        task["prompt"] = task["prompt"][:task["prompt"].find("```")]

    if "assert" in task["prompt"]:
        task["prompt"] = task["prompt"][:task["prompt"].find("assert")]
    return task
                
def test_report(dataset,lg):
    correct = 0
    for i in tqdm(range(len(dataset))):
        dataset[i]["full_code"] = process_humaneval_test(dataset[i], dataset, example_test=False,language=lg,test_case=False)
        result = check_correctness(dataset[i]["task_id"],dataset[i],lg,5,"./tmp")
        if result["passed"]==True:
            correct+=1
        dataset[i]["report_passed"] = result["passed"]
        dataset[i]["report_result"] = result["result"]
    print("==============Start Report Testing==============")
    correct_percent = correct/len(dataset)*100
    print(f"test_report, {correct_percent:0.2f}")
    return dataset
    
def test_agent(dataset,lg):
    correct = 0
    for i in tqdm(range(len(dataset))):
        test_case = [test for test in dataset[i]["test_case"].split("\n") if f"assert {dataset[i]['entry_point']}" in test]
        incorrect_tests = []
        correct_tests = []
        results = ""
        for test in test_case:
            dataset[i]["test_case"] = test
            dataset[i]["full_code"] = process_humaneval_test(dataset[i], dataset, example_test=False,language=lg,test_case=False)
            result = check_correctness(dataset[i]["task_id"],dataset[i],lg,5,"./tmp")
            if result["passed"]==True:
                correct+=1
            else:
                incorrect_tests.append(test)
            results += f"{test} -> {result['result']}\n"
        dataset[i]["incorrect_tests"] = "\n".join(incorrect_tests)
        dataset[i]["correct_tests"] = "\n".join(correct_tests)
        dataset[i]["result"] = results
    print("============Start Agent Testing=================")
    print("test_report",correct)
    return dataset


if __name__ == "__main__":
    model_list = ["gpt-3.5-turbo"]
    language = ["python"]
    for model in model_list:
        for lg in language:
            path = f"../dataset/humaneval_{model}_{lg}.json"
            with open(path, "r") as f:
                dataset = json.load(f)
            epoch = 5
            for current_epoch in range(epoch):
                dataset = test_agent(dataset,lg)
                dataset = call_fix_bug(dataset,model,lg)
                with open(f"../dataset/humaneval_{model}_{current_epoch}.json", "w") as f:
                    json.dump(dataset, f, indent=4)
            dataset = test_agent(dataset,lg)
            test_report(dataset,lg)
