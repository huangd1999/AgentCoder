import random
import json
from typing import Optional, Callable, Dict
import ast
import doctest
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
import numpy as np
import sys
sys.path.append('./CodeGeeX/')
import contextlib
import faulthandler
import io
import os
import multiprocessing
import platform
import signal
from tqdm import tqdm
from programmer_mbpp import fix_bug,call_fix_bug,call_completion,single_agent_helper
from codegeex.benchmark.utils import read_dataset, IMPORT_HELPER
from codegeex.benchmark.execution import check_correctness
import tempfile
correct_doctest = 0
correct_before_doctest = 0
correct_after_doctest = 0
result_original = 0
result_canonical_solution = 0
result_fuzzer = 0
result_fuzzer_canonical_solution = 0
idx_run_tests_orginal = []
idx_run_tests_canonical_solution = []
idx_run_tests_fuzzer = []
idx_run_tests_fuzzer_canonical_solution = []

language = ["python","cpp","js","go","js"]


def process_humaneval_test(sample, problems, example_test=False,language=language, test_case=True,canonical_solution=False):
    task_id = sample["task_id"]
    task_id = problems.index(sample)
    prompt = sample["prompt"]
    code = sample["completion"]
    if canonical_solution:
        code = sample["code"]
    # Pre-process for different languages
    if language == "python" or language == "py":
        if test_case:
            tests = sample["test_case"]
        else:
            test_case = sample["test_list"]
            tests = ""
            for test in test_case:
                tests+="\n"+test
        test_string = code + "\n" + tests
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

# def check_correctness_mbpp(code_string):


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
        dataset[i]["full_code"] = process_humaneval_test(dataset[i], dataset, example_test=False,language=lg,test_case=False)
        result = check_correctness(dataset[i]["task_id"],dataset[i],lg,5,"./tmp")
        if result["passed"]==True:
            correct+=1
        dataset[i]["result"] = result["result"]
        dataset[i]["passed"] = result["passed"]
    print("============Start Agent Testing=================")
    print("test_report",correct)
    return dataset

if __name__ == "__main__":
    model_list = ["gpt-3.5-turbo-1106"]
    language = ["python"]

    for model_name in model_list:
        for lg in language:
            path = f"./dataset/zero_shot_{model_name}_mbpp.json"
            with open(path, "r") as f:
                dataset = json.load(f)
            epoch = 5
            for current_epoch in range(epoch):
                print(lg,current_epoch)
                test_report(dataset,lg)
                test_agent(dataset,lg)
                dataset = call_completion(dataset,model_name,lg)
                with open(f"./dataset/zero_shot_{model_name}_{current_epoch}_mbpp.json", "w") as f:
                    json.dump(dataset, f, indent=4)
            with open(f"./dataset/zero_shot_{model_name}_{current_epoch}_mbpp_total.json", "w") as f:
                json.dump(dataset, f, indent=4)



