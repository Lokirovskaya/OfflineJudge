########### Config Here ###########

TESTCASE_PATH = 'testcase/'
SRC_DIR_PATH = 'aa.c'
COMPILE_TIMEOUT = 5
EXEC_TIMEOUT = 10

###################################

import os
import sys
import subprocess
import shutil
import atexit
import signal
import multiprocessing as mp
from typing import Union, Optional


COMPILER_TARGET_PATH = 'out/compiler.exe'

RED = '\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BOLD = '\x1b[1m'
END = '\x1b[0m'

def get_tests_names():
    test_set = set()
    for root, dirs, files in os.walk(TESTCASE_PATH):
        relative_path = os.path.relpath(root, TESTCASE_PATH)
        for file_name in files:
            file_path = os.path.join(relative_path, file_name.split('.')[0]).replace('\\', '/')
            test_set.add(file_path)
    test_list = sorted(list(test_set))
    return test_list


def compile_compiler():
    pass


def source_to_llvm(source_path, llvm_path) -> (bool, Optional[str]):
    args = [
        'clang',
        '-S',
        '-emit-llvm',
        '-xc',
        source_path,
        '-o',
        llvm_path,
        '-w'
    ]
    try:
        r = subprocess.run(args, timeout=COMPILE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return (
            False,
            f'{RED}{BOLD}Time Limit Exceeded{END}{RED}: Source -> LLVM IR ({COMPILE_TIMEOUT} s){END}'
        )

    if r.returncode != 0: 
        return (
            False,
            f'{RED}{BOLD}Runtime Error{END}{RED}: Source -> LLVM IR{END}'
        )
    return (True, None)


def llvm_to_exe(llvm_path, exe_path) -> (bool, Optional[str]):
    args = [
        'clang',
        llvm_path,
        'lib/lib.o',
        '-o',
        exe_path,
        '-O0'
    ]
    r = subprocess.run(args)
    if r.returncode != 0:
        return (
            False,
            f'{RED}{BOLD}Runtime Error{END}{RED}: LLVM IR -> ASM{END}'
        )
    return (True, None)


def run_exe(exe_path, input_path, answer_path) -> (bool, Union[str, int]):
    args = ['./' + exe_path]
    try:
        with open(answer_path, 'w') as answer_file:
            # stdin available
            if os.path.exists(input_path):
                with open(input_path, 'r') as input_file:
                    r = subprocess.run(args, stdin=input_file, stdout=answer_file, timeout=EXEC_TIMEOUT)
                    return (True, r.returncode)
            # no stdin
            else:
                r = subprocess.run(args, stdout=answer_file, timeout=EXEC_TIMEOUT)
                return (True, r.returncode)
    except subprocess.TimeoutExpired:
        return (
            False,
            f'{RED}{BOLD}Time Limit Exceeded{END}{RED}: Running ASM ({EXEC_TIMEOUT} s){END}'
        )


def check_answer(answer_path, correct_path, return_code) -> (bool, str):
    with open(answer_path, 'r') as answer_file:
        with open(correct_path, 'r') as correct_file:
            ans = answer_file.read()
            ans_lines = ans.rstrip().splitlines()
            correct = correct_file.read()
            correct_lines = correct.rstrip().splitlines()
            correct_return_code = int(correct_lines[-1])

            if return_code != correct_return_code:
                return (
                    False,
                    f'{RED}{BOLD}Wrong Answer{END}{RED}: Program return value error. Read {return_code} expected {correct_return_code}{END}'
                )
            for i in range(len(ans_lines)):
                if ans_lines[i].rstrip() != correct_lines[i].rstrip():
                    return (
                        False,
                        f'{RED}{BOLD}Wrong Answer{END}{RED}: First mismatch at line {i + 1}{END}'
                    ) 
            return (True, f'{GREEN}{BOLD}Accepted{END}')


def judge_one(test_name, idx, total) -> bool:
    input_path = f'testcase/{test_name}.in'
    source_path = f'testcase/{test_name}.sy'
    correct_path = f'testcase/{test_name}.out'
    
    test_name_no_dash = test_name.replace('/', '_')
    llvm_path = f'tmp/{test_name_no_dash}.ll'
    exe_path = f'tmp/{test_name_no_dash}.exe'
    answer_path = f'tmp/{test_name_no_dash}.out'

    while True:
        ok, msg = source_to_llvm(source_path, llvm_path)
        if not ok: break

        ok, msg = llvm_to_exe(llvm_path, exe_path)
        if not ok: break

        ok, msg = run_exe(exe_path, input_path, answer_path)
        if not ok: break
        else: return_val = msg

        ok, msg = check_answer(answer_path, correct_path, return_val)
        break

    print(f'{BOLD}({idx}/{total}){END} {test_name}: {msg}')
    return ok

        


def cleanup():
    shutil.rmtree('tmp/', ignore_errors=True)


def init():
    if not os.path.exists('out/'):
        os.makedirs('out/')
    if os.path.exists('tmp/'):
        shutil.rmtree('tmp/')
    os.makedirs('tmp/')

    def signal_handler(signal, frame):
        total = passed + failed
        print(f'\n{BOLD}Test Interrupted!{END} {GREEN}{BOLD}Accepted: ({passed}/{total}){END} {RED}{BOLD}Failed: ({failed}/{total}){END}')
        cleanup()
        sys.exit(0)

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    


if __name__ == '__main__':

    init()
    print(f'{BOLD}Compiling Java...{END}')
    compile_compiler()

    test_list = [(i + 1, test) for i, test in enumerate(get_tests_names())]
    print(f'{BOLD}Test start!{END} You can press Ctrl-C to cancel')

    num_cores = mp.cpu_count()
    print(f'{BOLD}Running on{END} {YELLOW}{BOLD}{num_cores}{END} {BOLD}cores!{END}')
    pool = mp.Pool(processes=num_cores)
    result_list = []
    for idx, test_name in test_list:
        result = pool.apply_async(judge_one, (test_name, idx, len(test_list)))
        result_list.append(result)
    pool.close()
    pool.join()

    result_list = [result.get() for result in result_list]
    passed = result_list.count(True)
    total = len(test_list)
              
    print(f'\n{BOLD}Test Finished!{END} {GREEN}{BOLD}Accepted: ({passed}/{total}){END} {RED}{BOLD}Failed: ({total - passed}/{total}){END}')
    cleanup()
    input('Press Enter to Exit')