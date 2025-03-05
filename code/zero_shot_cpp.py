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
        Prompt = [{"role": "user", "content": problems[task_id]["prompt"]}]
        code_all = generate_one_completion(task_id, Prompt)
        code = code_all[0]
        while(code == ""):
                    Prompt.append({"role": "assistant", "content": ""})
                    Prompt.append({"role": "user", "content": "Format fail"})
                    print("the code is null, regenerate")
                    code_all = generate_one_completion(task_id, Prompt)
                    code = code_all[0]
        if code[0] == " " and code[1] == " ":
            code = problems[task_id]["prompt"] + code
        samples = [
            dict(
                task_id = task_id,
                generation = code,
            )
        ]
        write_jsonl(ResultPath, samples, True)