########### Config Here ###########

TESTCASE_PATH = 'testcase/'
SRC_DIR_PATH = 'aa.c'
COMPILE_TIMEOUT = ''
EXEC_TIMEOUT = ''

###################################

import os
import sys
import subprocess

COMPILER_TARGET_PATH = 'out/compiler.exe'
answer_file = open('out/ans.out', 'w+')

RED = '\x1b[31m'
GREEN = '\x1b[32m'
BOLD = '\x1b[1m'
END = '\x1b[0m'

def get_judges_names():
    judge_set = set()
    for root, dirs, files in os.walk(TESTCASE_PATH):
        relative_path = os.path.relpath(root, TESTCASE_PATH)
        for file_name in files:
            file_path = os.path.join(relative_path, file_name.split('.')[0]).replace('\\', '/')
            judge_set.add(file_path)
    judge_list = sorted(list(judge_set))
    return judge_list


def compile_compiler():
    pass


def source_to_llvm(source_path):
    args = [
        'clang',
        '-S',
        '-emit-llvm',
        '-xc',
        source_path,
        '-o',
        'out/tmp.ll',
        '-w'
    ]
    r = subprocess.run(args)
    if r.returncode != 0: 
        print(f'{RED}{BOLD}Runtime Error{END}{RED}: Source -> LLVM IR{END}')
        return False
    return True


def llvm_to_exe():
    args = [
        'clang',
        'out/tmp.ll',
        'lib/lib.o',
        '-o',
        'out/tmp.exe',
        '-O0'
    ]
    r = subprocess.run(args)
    if r.returncode != 0:
        print(f'{RED}{BOLD}Runtime Error{END}{RED}: LLVM IR -> ASM{END}')
        return False
    return True


def run_exe(input_path):
    args = ['./out/tmp.exe']
    if os.path.exists(input_path):
        with open(input_path, 'r') as input_file:
            r = subprocess.run(args, stdin=input_file, stdout=answer_file)
            return r.returncode
    else:
        r = subprocess.run(args, stdout=answer_file)
        return r.returncode


def clear_answer_file():
    answer_file.truncate(0)


def check_answer(correct_path, return_code):
    with open(correct_path, 'r') as f:
        ans = answer_file.read()
        ans_lines = ans.rstrip().splitlines()
        correct = f.read()
        correct_lines = correct.rstrip().splitlines()
        correct_return_code = int(correct_lines[-1])

        if return_code != correct_return_code:
            return f'{RED}{BOLD}Wrong Answer{END}{RED}: Program return value error. Read {return_code} expected {correct_return_code}{END}'
        for i in range(len(ans_lines)):
            if ans_lines[i].rstrip() != correct_lines[i].rstrip():
                return f'{RED}{BOLD}Wrong Answer{END}{RED}: First mismatch at line {i + 1}{END}'
        return f'{GREEN}{BOLD}Accepted{END}'


folder_path = os.path.join(os.getcwd(), "out")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

compile_compiler()

judge_list = get_judges_names()
total = len(judge_list)
i = 0

for judge in judge_list:
    input_path = f'testcase/{judge}.in'
    source_path = f'testcase/{judge}.sy'
    correct_path = f'testcase/{judge}.out'

    i += 1
    print(f'({i}/{total}) {judge}: ', end='')
    sys.stdout.flush()

    clear_answer_file()

    if not source_to_llvm(source_path):
        continue

    if not llvm_to_exe():
        continue

    return_val = run_exe(input_path)
    msg = check_answer(correct_path, return_val)
    print(msg)
        
answer_file.close()
input('Press Enter to Exit')