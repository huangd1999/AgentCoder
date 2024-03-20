import random
import json
from typing import Optional, Callable, Dict
import ast
import contextlib
import faulthandler
import io
import os
import multiprocessing
import platform
import signal
from tqdm import tqdm
import tempfile

model_list = ["gpt-3.5-turbo"]
for model in model_list:
        
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

    result_original = 0
    result_canonical_solution = 0
    result_fuzzer = 0
    result_fuzzer_canonical_solution = 0
    idx_run_tests_orginal = []
    idx_run_tests_canonical_solution = []
    idx_run_tests_fuzzer = []
    idx_run_tests_fuzzer_canonical_solution = []

    def run_tests_orginal(i,problem):
        global result_original
        timeout = 2.0
        complete_function_code = (
            problem["prompt"] + problem['response'] + "\n" +
            problem["test"] + "\n" +
            f"check({problem['entry_point']})"
        )

        try:
            with swallow_io():
                with time_limit(timeout):
                    exec(complete_function_code, globals())
            problem["result"] = "pass"
        except TimeoutException:
            idx_run_tests_orginal.append(problem["task_id"])
            # print(problem["task_id"])
            # print("time out")
            result_original+=1
            problem["result"] = "time out"
        except BaseException as exc:
            idx_run_tests_orginal.append(problem["task_id"])
            result_original+=1
            # print("run_tests_orginal",problem["task_id"])
            # print("run_tests_orginal","Error in executing the code: " + str(exc))
            problem["result"] = "Error in executing the code: " + str(exc)
        
    def run_tests_canonical_solution(i,problem):
        global result_canonical_solution
        timeout = 7.0
        complete_function_code = (
            problem["prompt"] + problem['canonical_solution'] + "\n" +
            problem["test"] + "\n" +
            f"check({problem['entry_point']})"
        )
        try:
            with swallow_io():
                with time_limit(timeout):
                    exec(complete_function_code, globals())
            problem["result"] = "pass"
        except TimeoutException:
            idx_run_tests_canonical_solution.append(problem["task_id"])
            # print(problem["task_id"])
            # print("time out")
            result_canonical_solution+=1
            problem["result"] = "time out"
        except BaseException as exc:
            idx_run_tests_canonical_solution.append(problem["task_id"])
            result_canonical_solution+=1
            # print(problem["task_id"])
            # print("Error in executing the code: " + str(exc))
            problem["result"] = "Error in executing the code: " + str(exc)

    def run_tests_fuzzer(i,problem):
        global result_fuzzer
        timeout = 7.0

        complete_function_code = ( problem["prompt"] + problem['response'] + "\n" + problem["fuzzer_coverage"])

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
    lg = "python"
    path = f"./agent1/{model}_{lg}.json"
    with open(path, "r") as f:
        dataset = json.load(f)
    for i in tqdm(range(len(dataset))):
        task = dataset[i]
        # print(task)
        # run_tests_orginal(i,task)
        # run_tests_fuzzer_canonical_solution(i,task)
        # run_tests_fuzzer(i,task)
        run_tests_canonical_solution(i,task)
        
    print("=====================================")
    print(model,(1-result_original/len(dataset))*100)
    # print(result_original)
    # print(result_canonical_solution)
    # print(result_fuzzer_canonical_solution)
    # print(result_fuzzer)
    print("=====================================")

    with open(path, "w") as f:
        json.dump(dataset, f, indent=4)

    # print("=====================================")
    # print(idx_run_tests_orginal)
    # print("=====================================")
    # print(idx_run_tests_canonical_solution)
    # print("=====================================")
    # print(idx_run_tests_fuzzer_canonical_solution)
    # print("=====================================")
    # print(idx_run_tests_fuzzer)

    result_in_orginal_not_in_fuzzer = []

    for idx in idx_run_tests_fuzzer:
        if (idx in idx_run_tests_orginal):
            # print(idx)
            result_in_orginal_not_in_fuzzer.append(idx)

    # print(result_in_orginal_not_in_fuzzer)

