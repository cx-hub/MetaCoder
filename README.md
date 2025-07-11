Here are the code and data.

## Generate code
- `MetaCoder.py`

## Generate Function Call
- `get_function_call.py`

## Call LLMs
- `llmcaller.py`

## Other Python files
- Zero-Shot
- Few-Shot
- CoT

## Test
In test folder, run:
```bash
bash evaluate_humaneval_x.sh "Path to the jsonl file" cpp
```
or
```bash
bash evaluate_humaneval_x.sh "Path to the jsonl file" java
```

## Notice
- 1.Add API key to access LLMs.
- 2.Add Path to run the Python file.
- 3.There are lots C++ and Java library to add, or you will get a lower result. Our results are in data folder.
