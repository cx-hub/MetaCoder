import time
from datetime import datetime
from human_eval.data import write_jsonl, read_problems
from codegeex.benchmark.utils import read_dataset, IMPORT_HELPER
import subprocess

from llmcaller import call_model as call_llm

DataPath = "Path For Dataset, like HumanEval_CPP.jsonl"
ResultPath = "Path For Results, like data/GPT/GPt 3.5/CPP/1.jsonl"

problems = read_problems(DataPath)

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
            pos = gen.find("```cpp\n")
            if(pos != -1):
                gen = gen[pos+7:]
            pos = gen.find("```c++\n")
            if(pos != -1):
                gen = gen[pos+7:]
            pos = gen.find("```c\n")
            if(pos != -1):
                gen = gen[pos+5:]
            pos = gen.find("int main")
            while(pos != -1):
                gen = gen[:pos]
                pos = gen.find("int main")
            pos = gen.find("```")
            while(pos != -1):
                gen = gen[:pos]
                pos = gen.find("```")
            print("--------------------Generated Code-------------------")
            print(gen)
            return [gen, response[1], response[2]]
        except:
            print(f"Exception occurs, wait 30 seconds then retry...")
            time.sleep(30)

num_samples_per_task = 5
for _ in range(num_samples_per_task):
    for task_id in problems:
        the_task_name = task_id.replace("/","")
        Prompt = [
        {"role": "system", "content": 
         "## Role: You are a software programmer.\n"+
         "## Task: As a programmer, you are required to complete the function. Use a Chain-of-Thought approach to break down the problem, create pseudocode, and then write the code in C++ language.\n"+
         "## Code Formatting: \n" + "```cpp\n[Code]\n```\n"+
         "## Instructions:\n" +
         "1. **Understand and Clarify**: Make sure you understand the task.\n" + 
         "2. **Algorithm/Method Selection**: Decide on the most efficient way.\n" +
         "3. **Pseudocode Creation**: Write down the steps you will follow in pseudocode.\n" +
         "4. **Code Generation**: Translate your pseudocode into executable C++ code.\n" +
         "# Example 1:\n"+
         "## Problem:\n" +
         "int minRectanglesToCoverPoints(vector<vector<int>>& points, int w){\n```You are given a 2D integer array points, where points[i] = [xi, yi]. You are also given an integer w. Your task is to cover all the given points with rectangles. Each rectangle has its lower end at some point (x1, 0) and its upper end at some point (x2, y2), where x1 <= x2, y2 >= 0, and the condition x2 - x1 <= w must be satisfied for each rectangle. A point is considered covered by a rectangle if it lies within or on the boundary of the rectangle. Return an integer denoting the minimum number of rectangles needed so that each point is covered by at least one rectangle. Note: A point may be covered by more than one rectangle.```\n" +
         "## Response:\n" + 
         "```cpp\n#include <vector>\n#include <algorithm>\nint minRectanglesToCoverPoints(std::vector<std::vector<int>>& points, int w) {\n    std::sort(points.begin(), points.end(), [](const std::vector<int>& a, const std::vector<int>& b) {\n        return a[0] < b[0];\n    });\n    int numRectangles = 0;\n    int currentEnd = -1;\n    for (const std::vector<int>& point : points) {\n        int x = point[0];\n        if (x > currentEnd) {\n            numRectangles++;\n            currentEnd = x + w;\n        }\n    }\n    return numRectangles;\n}```\n"+
         "# Example 2:\n"+
         "## Problem:\n" +
         "/*\nFrom a supplied vector of numbers (of length at least two) select and return two that are the closest to each\nother and return them in order (smaller number, larger number).\n>>> find_closest_elements({1.0, 2.0, 3.0, 4.0, 5.0, 2.2})\n(2.0, 2.2)\n>>> find_closest_elements({1.0, 2.0, 3.0, 4.0, 5.0, 2.0})\n(2.0, 2.0)\n*/\n#include<stdio.h>\n#include<math.h>\n#include<vector>\nusing namespace std;\nvector<float> find_closest_elements(vector<float> numbers){\n" +
         "## Response:\n" + 
         "```cpp\n#include<stdio.h>\n#include<math.h>\n#include<vector>\nusing namespace std;\nvector<float> find_closest_elements(vector<float> numbers){\n    vector<float> out={};\n    for (int i=0;i<numbers.size();i++)\n    for (int j=i+1;j<numbers.size();j++)\n        if (out.size()==0 or abs(numbers[i]-numbers[j])<abs(out[0]-out[1]))\n            out={numbers[i],numbers[j]};\n    if (out[0]>out[1])\n        out={out[1],out[0]};\n    return out;\n}\n```\n"
         },
        {"role": "user", "content": "## Problem:\n" + problems[task_id]["prompt"]}]
        code_all = generate_one_completion(task_id, Prompt)
        code = code_all[0]
        while(code == ""):
                    Prompt.append({"role": "assistant", "content": ""})
                    Prompt.append({"role": "user", "content": "Format fail"})
                    print("the code is null, regenerate")
                    code_all = generate_one_completion(task_id, Prompt)
                    code = code_all[0]
        samples = [
            dict(
                task_id = task_id,
                generation = code,
            )
        ]
        write_jsonl(ResultPath, samples, True)
