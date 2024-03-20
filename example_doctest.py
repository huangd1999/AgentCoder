from typing import List
import doctest
import io
import sys


from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool: 
    """
    Check if in given list of numbers, are any two numbers closer to each other than given threshold.
    """
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    for idx, elem in enumerate(numbers): 
        for idx2, elem2 in enumerate(numbers): 
            if idx != idx2: 
                distance = abs(elem - elem2) 
                if distance < threshold: 
                    return True 
    return False


# 1. Basic Test Cases:
assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False
# # exec(code_function)

# # 创建一个StringIO对象来捕获输出
# output = io.StringIO()
# sys.stdout = output  # 重定向标准输出到StringIO对象

# doctest.run_docstring_examples(has_close_elements, globals())  # 这将运行所有的测试，并将输出发送到我们的StringIO对象

# sys.stdout = sys.__stdout__  # 重置标准输出到原来的位置

# # 获取捕获的输出
# result = output.getvalue()
# output.close()

# # 打印或以其他方式使用result变量
# print(result)
# # print("result:\n",result)


# # from typing import List
# # import doctest
# # import io
# # import sys


# # from typing import List

# # def has_close_elements(numbers: List[float], threshold: float) -> bool: 
# #     """
# #     Check if in given list of numbers, are any two numbers closer to each other than given threshold.
# #     >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
# #     False
# #     >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
# #     True
# #     """
# #     for idx, elem in enumerate(numbers): 
# #         for idx2, elem2 in enumerate(numbers): 
# #             if idx != idx2: 
# #                 distance = abs(elem - elem2) 
# #                 if distance < threshold: 
# #                     return True 
# #     return False
# # doctest.testmod()

def sort_array(arr):
    """
    In this Kata, you have to sort an array of non-negative integers according to
    number of ones in their binary representation in ascending order.
    For similar number of ones, sort based on decimal value.

    It must be implemented like this:
    >>> sort_array([1, 5, 2, 3, 4]) == [1, 2, 3, 4, 5]
    >>> sort_array([-2, -3, -4, -5, -6]) == [-6, -5, -4, -3, -2]
    >>> sort_array([1, 0, 2, 3, 4]) [0, 1, 2, 3, 4]
    """
    return sorted(sorted(arr), key=lambda x: bin(x)[2:].count('1'))


def test_sort_array(sort_array):
    # Basic Test Cases:
    assert sort_array([1, 5, 2, 3, 4]) == [1, 2, 3, 4, 5], "Test Case 1 Failed"
    assert sort_array([-2, -3, -4, -5, -6]) == [-6, -5, -4, -3, -2], "Test Case 2 Failed"
test_sort_array(sort_array)