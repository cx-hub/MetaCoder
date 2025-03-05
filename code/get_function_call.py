import time
from datetime import datetime
from openai import OpenAI
from human_eval.data import write_jsonl, read_problems
from codegeex.benchmark.utils import IMPORT_HELPER
import subprocess
import threading
import os
import re

from llmcaller import call_model as call_llm

DataPath = "Path For Dataset, like HumanEval_CPP.jsonl"
FunctionCallPath = "Path For FunctionCall, like test/dataset/function call/CPP.jsonl"
TmpPath = "Path for compiling the tmp code, like ../tmp.cpp"

problems = read_problems(DataPath)


# CPP
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
            return gen
        except:
            print(f"Exception occurs, wait 30 seconds then retry...")
            time.sleep(30)

for task_id in problems:
        Prompt = [
        {"role": "system", "content": 
         "## Role: You are a software programmer.\n"+
         "## Task: As a programmer, you are required to generate an input for the uncompleted function.\n"
        },
        {"role": "user", "content": 
         "## Problem:\n" + "/*\nReturn the result of a**0.5+1.\n*/\n#include <bits/stdc++.h>\nusing namespace std;\nfloat func(int a){\n"
         },
         {"role": "assistant", "content": 
         "func(1);"
         },
         {"role": "user", "content": 
         "## Problem:\n" + "/*\nReturn the result of a**2+1 and a + 1 in order(a + 1, a**2+1).\n*/\n#include<vector>\nusing namespace std;\nvector<float> func(float a){\n"
         },
         {"role": "assistant", "content": 
         "func(1);"
         },
        {"role": "user", "content": "## Problem:\n" + problems[task_id]["prompt"]}]

        
        the_input = generate_one_completion(task_id, Prompt)

        test_set_up = ""
        for s in IMPORT_HELPER["cpp"]:
            if s not in problems[task_id]["prompt"]:
                test_set_up += s + "\n"
        test_code = test_set_up + problems[task_id]["prompt"] + "}\nint main(){" + the_input + "return 0;}"
        with open(TmpPath, 'w',encoding="utf-8") as f:
            f.write(test_code)

        compilation_result = subprocess.run(["g++", TmpPath], timeout=10, capture_output=True)
        compile_returncode = compilation_result.returncode
        while((compile_returncode != 0) or (problems[task_id]["entry_point"] not in the_input)):
            Prompt.append({"role": "assistant", "content": the_input})
            Prompt.append({"role": "user", "content": "Just need to generate one input. You may fail the function name or input format. Check the name of the uncompleted function and the input format."})
            print("code is null or unexe\n")
            the_input = generate_one_completion(task_id, Prompt)
            test_code = test_set_up + problems[task_id]["prompt"] + "}\nint main(){" + the_input + "return 0;}"
            with open(TmpPath, 'w',encoding="utf-8") as f:
                f.write(test_code)
            compilation_result = subprocess.run(["g++", TmpPath], timeout=10, capture_output=True)
            compile_returncode = compilation_result.returncode

        samples = [
            dict(
                task_id = task_id,
                the_input = the_input
            )
        ]
        write_jsonl(FunctionCallPath, samples, True)

# Java

