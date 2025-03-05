import time
from datetime import datetime
from openai import OpenAI
from human_eval.data import write_jsonl, read_problems
from codegeex.benchmark.utils import IMPORT_HELPER
import subprocess
import threading
import os

from llmcaller import call_model as call_llm

DataPath = "Path For Dataset, like HumanEval_CPP.jsonl"
FunctionCallPath = "Path For FunctionCall, like test/dataset/function call/CPP.jsonl"
TmpPath = "Path for compiling the tmp code, like ../a.cpp"
TmpResultPath = "Path for tmp result, like ../tmp/"
ResultPath = "Path For Results, like data/GPT/GPt 3.5/CPP/1.jsonl"


problems = read_problems(DataPath)
my_input = read_problems(FunctionCallPath)

def generate_one_completion(task_id, prompt):
    while True:
        print(datetime.now().strftime("%H:%M:%S"), task_id)
        try:
            response = call_llm(prompt)
            gen = response[0]
            the = "</think>"
            pos = gen.find(the)
            while(pos != -1):
                gen = gen[pos+10:]
                pos = gen.find(the)
            the = "```cpp\n"
            pos = gen.find(the)
            while(pos != -1):
                gen = gen[pos+7:]
                pos = gen.find(the)
            pos = gen.find("```")
            if(pos != -1):
                gen = gen[:pos]
            pos = gen.find("int main")
            if(pos != -1):
                gen = gen[:pos]
            pos = gen.find("// Example usage")
            if(pos != -1):
                gen = gen[:pos]
            pos = gen.find("# Example usage")
            if(pos != -1):
                gen = gen[:pos]
            print(gen)
            print("==========================================")
            return gen
        except:
            print(f"Exception occurs, wait 30 seconds then retry...")
            time.sleep(30)

def generate_one_completion_py(task_id, prompt):
    while True:
        print(datetime.now().strftime("%H:%M:%S"), task_id)
        try:
            response = call_llm(prompt)
            gen = response[0]
            the = "</think>"
            pos = gen.find(the)
            while(pos != -1):
                gen = gen[pos+10:]
                pos = gen.find(the)
            the = "```python\n"
            pos = gen.find(the)
            while(pos != -1):
                gen = gen[pos+10:]
                pos = gen.find(the)
            pos = gen.find("### Second step")
            if(pos != -1):
                gen = gen[:pos]
            pos = gen.find("```")
            if(pos != -1):
                gen = gen[:pos]
            pos = gen.find("# Test cases")
            if(pos != -1):
                gen = gen[:pos]
            pos = gen.find("// Example usage")
            if(pos != -1):
                gen = gen[:pos]
            pos = gen.find("# Example usage")
            if(pos != -1):
                gen = gen[:pos]
            print(gen)
            return gen
        except:
            print(f"Exception occurs, wait 30 seconds then retry...")
            time.sleep(30)

def regenerate_err(the_problem,task_id,err,the_code,try_n = 3):
        prompt = [
                {"role": "system", "content": "**Role**: You are a software programmer.\n"+
                 "**Task**: As a programmer, you are required to fix the compile bug, the main() function is right so just care about the content before the main().\n"+
                 "**Code Formatting**: Must write code in \n"+
                 "```cpp\n[Code]\n```\nformat."+
                 "# For example:\n"+
                 "```cpp\n#include<stdio.h>\nusing namespace std;\nint func(int a){\n    int b = a + 1;\n    return b;\n}\n```"},
                 {"role": "user", "content": "Donot change the function declaration in problem.\n## Problem:\n" + the_problem},
                 {"role": "assistant", "content": "## C++ code solution:\n" + the_code},
                 {"role": "user", "content": "Donot change the function declaration in problem.\n## Compile bug information:\n" + err}]
        while(try_n > 0):
            try_n = try_n - 1
            the_task_name = task_id.replace("/","")
            the_gen = generate_one_completion(task_id, prompt)
            while(the_gen == ""):
                    prompt.append({"role": "assistant", "content": ""})
                    prompt.append({"role": "user", "content": "Format fail"})
                    print("the code is null, regenerate")
                    the_gen = generate_one_completion(task_id, prompt)
            test_set_up = ""
            for s in IMPORT_HELPER["cpp"]:
                if s not in the_gen:
                    test_set_up += s + "\n"
            test_code = test_set_up + the_gen + "\n" + "int main(){"+ my_input[task_id]["the_input"] + "return 0;}"
            with open(TmpPath.replace("a",the_task_name), 'w',encoding="utf-8") as f:
                f.write(test_code)

            if "162" in task_id:
                compilation_result = subprocess.run(["g++", TmpPath.replace("a",the_task_name), "-std=c++11", "-lcrypto", "-lssl"], timeout=50, capture_output=True)
            else:
                compilation_result = subprocess.run(["g++", TmpPath.replace("a",the_task_name), "-std=c++11"], timeout=50, capture_output=True)
            compile_returncode = compilation_result.returncode
            
            print(compile_returncode)
            if(compile_returncode == 0):
                the_code = the_gen
                break
            if compilation_result.stderr:
                err = compilation_result.stderr.decode()
            else:
                err = compilation_result.stdout.decode()
            prompt.append({"role": "assistant", "content": "## C++ code solution:\n"+the_gen})
            prompt.append({"role": "user", "content": "Donot change the declaration in problem.\n## Compile bug information:\n"+err[:min(len(err),5000)]})

        return the_code

def generate_answer(problems,task_id):
        the_task_name = task_id.replace("/","")
        Prompt = [{"role": "system", "content": 
         "**Role**: You are a software programmer, and you are good at completing python code and C++ code to solve problem.\n" +
         "**Task**: As a programmer, you are required to use a step-by-step approach to solve the problem as the followed steps: " +
         "First step, write python code to solve the problem; Second step, analyse how the python code that you write can solve this problem; Third step, write the C++ solution according to the python solution and the python code summary.\n"+
         "**Note for writting C++**: \n" + 
         "1. When calling a function, make sure the function is available in C++.\n"+
         "2. Pay attention to variable types.\n" + 
         "3. Pay attention to C++ syntax conventions and refrain from defining functions within functions.\n" + 
         "4. Donot change the declaration in problem, like 'vector<float>' to 'pair<float, float>'.\n" + 
         "# Example 1:\n"+
         "## Problem:\n" +
         "int minRectanglesToCoverPoints(vector<vector<int>>& points, int w){\n```You are given a 2D integer array points, where points[i] = [xi, yi]. You are also given an integer w. Your task is to cover all the given points with rectangles. Each rectangle has its lower end at some point (x1, 0) and its upper end at some point (x2, y2), where x1 <= x2, y2 >= 0, and the condition x2 - x1 <= w must be satisfied for each rectangle. A point is considered covered by a rectangle if it lies within or on the boundary of the rectangle. Return an integer denoting the minimum number of rectangles needed so that each point is covered by at least one rectangle. Note: A point may be covered by more than one rectangle.```\n" +
         "### First step, generate python code to solve the problem:\n" +
         "```python\ndef minRectanglesToCoverPoints(points, w):\n    points.sort()\n    rectangles_count = 0\n    n = len(points)\n    i = 0\n    while i < n:\n        xi, yi = points[i]\n        max_x_range = xi + w\n        while i < n and points[i][0] <= max_x_range:\n            i += 1\n        rectangles_count += 1\n    return rectangles_count```\n"
         "### Second step, analyse the python code:\n" +
         "```The code defines a function that calculates the minimum number of rectangles needed to cover a set of points on a 2D plane. The points are given as a list of x and y coordinates, and each rectangle has a fixed width (w). The function first sorts the points based on their x-coordinates. It then iterates through the points, placing a rectangle starting at the current point and extending to cover points within the width range. The loop continues until all points are covered, and the function returns the total number of rectangles used.```\n"
         "### Last step, generate C++ solution according to the python solution and the python code summary:\n" +
         "```cpp\n#include <vector>\n#include <algorithm>\nint minRectanglesToCoverPoints(std::vector<std::vector<int>>& points, int w) {\n    std::sort(points.begin(), points.end(), [](const std::vector<int>& a, const std::vector<int>& b) {\n        return a[0] < b[0];\n    });\n    int numRectangles = 0;\n    int currentEnd = -1;\n    for (const std::vector<int>& point : points) {\n        int x = point[0];\n        if (x > currentEnd) {\n            numRectangles++;\n            currentEnd = x + w;\n        }\n    }\n    return numRectangles;\n}```\n"
         "# Example 2:\n"+
         "## Problem:\n" +
         "/*\nFrom a supplied vector of numbers (of length at least two) select and return two that are the closest to each\nother and return them in order (smaller number, larger number).\n>>> find_closest_elements({1.0, 2.0, 3.0, 4.0, 5.0, 2.2})\n(2.0, 2.2)\n>>> find_closest_elements({1.0, 2.0, 3.0, 4.0, 5.0, 2.0})\n(2.0, 2.0)\n*/\n#include<stdio.h>\n#include<math.h>\n#include<vector>\nusing namespace std;\nvector<float> find_closest_elements(vector<float> numbers){\n" +
         "### First step, generate python code to solve the problem:\n" +
         "```python\nfrom typing import List\n\n\ndef find_closest_elements(numbers):\n    numbers.sort()\n    min_diff = float('inf')\n    result = (0, 0)\n    for i in range(len(numbers) - 1):\n        diff = numbers[i+1] - numbers[i]\n        if diff < min_diff:\n            min_diff = diff\n            result = (numbers[i], numbers[i+1])\n    return result\n```\n"
         "### Second step, analyse the python code:\n" +
         "```The Python code defines a function that takes a list of numbers as input and returns a tuple containing the two numbers that are closest to each other in the list. The function first sorts the input list in ascending order. It then initializes variables `min_diff` to positive infinity and `result` to (0, 0) to keep track of the minimum difference and the pair of closest elements found so far. \n\nThe function then iterates through the sorted list and calculates the difference between each pair of adjacent numbers. If the calculated difference is less than the current minimum difference, it updates the minimum difference and the result tuple to the current pair of numbers. Finally, the function returns the result tuple containing the two closest elements.```\n"
         "### Last step, generate C++ solution according to the python solution and the python code summary:\n" +
         "```cpp\n#include<stdio.h>\n#include<math.h>\n#include<vector>\nusing namespace std;\nvector<float> find_closest_elements(vector<float> numbers){\n    vector<float> out={};\n    for (int i=0;i<numbers.size();i++)\n    for (int j=i+1;j<numbers.size();j++)\n        if (out.size()==0 or abs(numbers[i]-numbers[j])<abs(out[0]-out[1]))\n            out={numbers[i],numbers[j]};\n    if (out[0]>out[1])\n        out={out[1],out[0]};\n    return out;\n}\n```\n"
         },
         {"role": "user", "content": "## Problem:\n" + problems[task_id]["prompt"] +
          "\n### First step, generate python code to solve the problem."}]
        while True:
            try:
                py_code = generate_one_completion_py(task_id, Prompt)
                while(py_code == ""):
                    print("regenerate python code")
                    py_code = generate_one_completion_py(task_id, Prompt)
                break
            except:
                print(f"get python failed, wait 30 seconds then retry...\n")
                time.sleep(30)

        print(py_code+"\n")
        Prompt.append({"role": "assistant", "content": py_code})
        Prompt.append({"role": "user", "content": "### Second step, analyse the python code you generated."})
        while True:
            try:
                my_summary = call_llm(Prompt)[0]
                the = "</think>"
                pos = my_summary.find(the)
                while(pos != -1):
                    my_summary = my_summary[pos+10:]
                    pos = my_summary.find(the)
                pos = my_summary.find("### Third step")
                while(pos != -1):
                    my_summary = my_summary[:pos]
                    pos = my_summary.find("### Third step")
                pos = my_summary.find("### Last step")
                while(pos != -1):
                    my_summary = my_summary[:pos]
                    pos = my_summary.find("### Last step")
                pos = my_summary.find("### C++ Solution")
                while(pos != -1):
                    my_summary = my_summary[:pos]
                    pos = my_summary.find("### C++ Solution")
                pos = my_summary.find("```cpp\n")
                while(pos != -1):
                    my_summary = my_summary[:pos]
                    pos = my_summary.find("```cpp\n")
                
                break
            except:
                print(f"get summary failed, wait 1 seconds then retry...\n")
                time.sleep(1)

        print(my_summary)
        Prompt.append({"role": "assistant", "content": my_summary})
        Prompt.append({"role": "user", "content": "### Last step, generate C++ solution according to the python solution and the python code summary. Donot change the function declaration in problem." + problems[task_id]["prompt"]})

        
        code = generate_one_completion(task_id, Prompt)
        while(code == ""):
            print("the code is null, regenerate")
            code = generate_one_completion(task_id, Prompt)
        test_set_up = ""
        for s in IMPORT_HELPER["cpp"]:
            if s not in code:
                test_set_up += s + "\n"
        test_code = test_set_up + code + "\n" + "int main(){"+ my_input[task_id]["the_input"] + "return 0;}"

        with open(TmpPath.replace("a",the_task_name), 'w',encoding="utf-8") as f:
            f.write(test_code)

        if "162" in task_id:
            compilation_result = subprocess.run(["g++", TmpPath.replace("a",the_task_name), "-lcrypto", "-lssl"], timeout=50, capture_output=True)
        else:
            compilation_result = subprocess.run(["g++", TmpPath.replace("a",the_task_name)], timeout=50, capture_output=True)
        compile_returncode = compilation_result.returncode

        the_len = 5000
        if(compile_returncode!=0):
            if compilation_result.stderr:
                err = compilation_result.stderr.decode()
            else:
                err = compilation_result.stdout.decode()
            print("regenerate the code to pass compile")
            code = regenerate_err(problems[task_id]["prompt"],task_id,err[:min(len(err),the_len)],code,try_n = 3, flag=1)
                samples = [
            dict(
                task_id=task_id,
                generation=code,
                py_code = py_code,
                py_summary = my_summary
            )
        ]
        write_jsonl(TmpResultPath + task_id.replace("/","") + ".jsonl", samples, True)

num_samples_per_task = 5
thread_num = 1
the_problem = []

for task_id in problems:
    the_problem.append(task_id)

for _ in range(num_samples_per_task):
        threads= [threading.Thread(target=generate_answer,args=(problems, the_problem[thread_num*i + j])) for j in range(thread_num)]
        for t in threads:
            t.setDaemon(True)
            t.start()
        for t in threads:
            t.join()

        files= os.listdir(TmpResultPath)
        for file in files:
            if not os.TmpResultPath.isdir(file):
                my_code_tmp = read_problems(TmpResultPath + file)
                for task_id in my_code_tmp:
                    samples = [
                        dict(
                            task_id=task_id,
                            generation=my_code_tmp[task_id]["generation"],
                            # py_code = my_code_tmp[task_id]["py_code"],
                            # py_summary = my_code_tmp[task_id]["py_summary"]
                        )
                    ]
                    write_jsonl(ResultPath, samples, True)

            
                os.remove(TmpResultPath + file)

