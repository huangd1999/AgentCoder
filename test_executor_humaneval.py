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
sys.path.append('./CodeGeeX/')
import contextlib
import faulthandler
import io
import os
import multiprocessing
import platform
import signal
from tqdm import tqdm
from programmer_humaneval import fix_bug,call_fix_bug
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
        # for line in code.split("\n"):
        #     if (len(line.strip()) > 0 and line[0] != ' ' and line[0] != '\t'):
        #         break
        #     code_.append(line)
        # code = "\n".join(code_)
        test_setup = "\n".join(IMPORT_HELPER["python"]) + "\n"
        if f"class sample['entry_point']" in code:
            test_string = test_setup + code + "\n" + test + "\n" + f"check({sample['entry_point']})"
        else:
            test_string = test_setup + prompt + code + "\n" + test + "\n" + f"check({sample['entry_point']})"
        # test_string = prompt+code+"\n"+sample["test_case"]
        # test_string = sample["completion"]+"\n"+sample["test_case"]
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

def run_tests_orginal(i,problem):
    global result_original
    timeout = 2.0
    # complete_function_code = (
    #     problem["prompt"] + problem['completion'] + "\n" +
    #     problem["test"] + "\n" +
    #     f"check({problem['entry_point']})"
    # )
    if f"def {problem['entry_point']}" in problem['completion']:
        complete_function_code = (
            problem['completion'] + "\n" +
            problem["test_case"]
        )
    else:
        complete_function_code = (
            problem["prompt"] + problem['completion'] + "\n" +
            problem["test_case"]
        )

    try:
        with swallow_io():
            with time_limit(timeout):
                exec(complete_function_code, globals())
        problem["result"] = "pass"
        result_original+=1
    except Exception as exc:
        idx_run_tests_orginal.append(problem["task_id"])
        # print("run_tests_orginal",problem["task_id"])
        # print("run_tests_orginal","Error in executing the code: " + str(exc))
        problem["result"] = "Error in executing the code: " + str(exc)
        # print(problem["result"])
        print(problem["task_id"],problem["result"])

                
    
def run_tests_canonical_solution(i,problem):
    global result_canonical_solution
    timeout = 2.0
    complete_function_code = (
        problem["prompt"] + problem['canonical_solution'] + "\n" +
        problem["test_case"]
        # "\n" +
        # f"check({problem['entry_point']})"
    )
    try:
        with swallow_io():
            with time_limit(timeout):
                exec(complete_function_code, globals())
        problem["result"] = "pass"
        result_canonical_solution+=1
    except Exception as exc:
        idx_run_tests_canonical_solution.append(problem["task_id"])
        # print(problem["task_id"])
        
        # problem["result"] = "Error in executing the code: " + str(exc)
        if "Basic Test Case" in str(exc):
            print(problem["task_id"],"Error in executing the code: " + str(exc))
        else:
            result_canonical_solution+=1

def run_tests_fuzzer(i,problem):
    global result_fuzzer
    timeout = 7.0

    complete_function_code = ( problem["prompt"] + problem['completion'] + "\n" + problem["fuzzer_coverage"])

    try:
        with swallow_io():
            with time_limit(timeout):
                exec(complete_function_code, globals())
        problem["result"] = "pass"
    except TimeoutException:
        idx_run_tests_fuzzer.append(problem["task_id"])
        # print(problem["task_id"])
        # print("time out")
        result_fuzzer+=1
        problem["result"] = "time out"
    except BaseException as exc:
        idx_run_tests_fuzzer.append(problem["task_id"])
        result_fuzzer+=1
        # print(problem["task_id"])
        # print("Error in executing the code: " + str(exc))
        problem["result"] = "Error in executing the code: " + str(exc)
    
    return problem

def run_tests_fuzzer_canonical_solution(i,problem):
    global result_fuzzer_canonical_solution
    timeout = 7.0
    complete_function_code = ( problem["prompt"] + problem['canonical_solution'] + "\n" + problem["fuzzer_coverage"])
    try:
        with swallow_io():
            with time_limit(timeout):
                exec(complete_function_code, globals())
        problem["result"] = "pass"
    except TimeoutException:
        idx_run_tests_fuzzer_canonical_solution.append(problem["task_id"])
        # print(problem["task_id"])
        # print("time out")
        result_fuzzer_canonical_solution+=1
        problem["result"] = "time out"
    except BaseException as exc:
        idx_run_tests_fuzzer_canonical_solution.append(problem["task_id"])
        result_fuzzer_canonical_solution+=1
        # print(problem["task_id"])
        # print("Error in executing the code: " + str(exc))
        problem["result"] = "Error in executing the code: " + str(exc)



def test_report(dataset,lg):
    correct = 0
    for i in tqdm(range(len(dataset))):
        dataset[i]["full_code"] = process_humaneval_test(dataset[i], dataset, example_test=False,language=lg,test_case=False)
        result = check_correctness(dataset[i]["task_id"],dataset[i],lg,5,"./tmp")
        if result["passed"]==True:
            correct+=1
    print("==============Start Report Testing==============")
    print("test_report",correct)
    
def test_agent(dataset,lg):
    correct = 0
    for i in tqdm(range(len(dataset))):
        if "passed" in dataset[i].keys() and dataset[i]["passed"]==True:
            correct+=1
            continue
        dataset[i]["full_code"] = process_humaneval_test(dataset[i], dataset, example_test=False,language=lg,test_case=True)
        result = check_correctness(dataset[i]["task_id"],dataset[i],lg,5,"./tmp")
        if result["passed"]==True:
            correct+=1
        dataset[i]["result"] = result["result"]
        dataset[i]["passed"] = result["passed"]
    print("============Start Agent Testing=================")
    print("test_report",correct)


# model_list = ["gpt-3.5-turbo","gpt-3.5-turbo-0301","palm-2-codechat-bison","claude-instant-1"]
model_list = ["gpt-3.5-turbo"]
# language = ["js", "java", "go", "cpp","python"]
language = ["python"]
for model in model_list:
    for lg in language:
        path = f"./dataset/{model}_{lg}.json"
        with open(path, "r") as f:
            dataset = json.load(f)
        epoch = 5
        for _ in range(epoch):
            test_report(dataset,lg)
            test_agent(dataset,lg)
            dataset = call_fix_bug(dataset,model,lg)
        test_report(dataset,lg)
        test_agent(dataset,lg)
        
        with open(f"./dataset/{lg}/{model}_{lg}_{epoch}.json", "w") as f:
            json.dump(dataset, f)
