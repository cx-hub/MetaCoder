# This script is for evaluating the functional correctness of the generated codes of HumanEval-X.

INPUT_FILE=$1  # Path to the .jsonl file that contains the generated codes.
LANGUAGE=$2  # Target programming language, currently support one of ["python", "java", "cpp", "js", "go"]
N_WORKERS=$3  # Number of parallel workers.
TIMEOUT=$4  # Timeout in seconds.

SCRIPT_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
MAIN_DIR=$(dirname "$SCRIPT_DIR")

echo "$INPUT_FILE"

if [ -z "$N_WORKERS" ]
then
    N_WORKERS=15
fi

if [ -z "$LANGUAGE" ]
then
    LANGUAGE=python
fi

if [ -z "$TIMEOUT" ]
then
    TIMEOUT=30
fi

DATA_DIR=$MAIN_DIR/test/dataset/humaneval_$LANGUAGE.jsonl

if [ $LANGUAGE = cpp ]; then
  export PATH=$PATH:/usr/bin/openssl
fi

CMD="python $MAIN_DIR/test/evaluate_humaneval_x.py \
    --input_file "$INPUT_FILE" \
    --n_workers $N_WORKERS \
    --tmp_dir $MAIN_DIR/test/tmp/ \
    --problem_file $DATA_DIR \
    --timeout $TIMEOUT"

echo "$CMD"
eval "$CMD"
