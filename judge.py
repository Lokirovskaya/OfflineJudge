########### Config Here ###########

TESTCASE_PATH = 'testcase/'
SRC_DIR_PATH = 'aa.c'
COMPILE_TIMEOUT = 5
EXEC_TIMEOUT = 20

###################################

import os
import sys
import subprocess as sp
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
        r = sp.run(args, timeout=COMPILE_TIMEOUT, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    except sp.TimeoutExpired:
        return (
            False,
            f'{YELLOW}{BOLD}Time Limit Exceeded{END}{YELLOW}: Source -> LLVM IR ({COMPILE_TIMEOUT} s){END}'
        )

    if r.returncode != 0: 
        return (
            False,
            f'{YELLOW}{BOLD}Runtime Error{END}{YELLOW}: Source -> LLVM IR{END}'
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
    r = sp.run(args, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    if r.returncode != 0:
        return (
            False,
            f'{YELLOW}{BOLD}Runtime Error{END}{YELLOW}: LLVM IR -> ASM{END}'
        )
    return (True, None)


def run_exe(exe_path, input_path, answer_path) -> (bool, Optional[str], Optional[int], Optional[str]):
    args = ['./' + exe_path]
    try:
        with open(answer_path, 'w') as answer_file:
            # stdin available
            if os.path.exists(input_path):
                with open(input_path, 'r') as input_file:
                    r = sp.run(args, stdin=input_file, stdout=sp.PIPE, stderr=sp.DEVNULL, timeout=EXEC_TIMEOUT)
                    return (True, r.stdout, r.returncode, None)
            # no stdin
            else:
                r = sp.run(args, stdout=sp.PIPE, stderr=sp.DEVNULL, timeout=EXEC_TIMEOUT)
                return (True, r.stdout, r.returncode, None)
    except sp.TimeoutExpired:
        return (
            False,
            None,
            None,
            f'{YELLOW}{BOLD}Time Limit Exceeded{END}{YELLOW}: Running ASM ({EXEC_TIMEOUT} s){END}'
        )


def check_answer(answer_str, correct_path, return_code, wa_path) -> (bool, str):
    with open(correct_path, 'r') as correct_file:
        ans_lines = answer_str.rstrip().splitlines()
        ans_lines.append(str(return_code))

        correct = correct_file.read()
        correct_lines = correct.rstrip().splitlines()

        min_len = min(len(ans_lines), len(correct_lines))
        for i in range(min_len):
            if ans_lines[i].rstrip() != correct_lines[i].rstrip():
                return (
                    False,
                    f'{RED}{BOLD}Wrong Answer{END}{RED}: Line {i + 1}{END}'
                )
        if len(ans_lines) != min_len:
            return (
                False,
                f'{RED}{BOLD}Wrong Answer{END}{RED}: Line {min_len + 1}{END}'
            )
        return (True, f'{GREEN}{BOLD}Accepted{END}')


def judge_one(test_name, idx, total) -> bool:
    input_path = f'testcase/{test_name}.in'
    source_path = f'testcase/{test_name}.sy'
    correct_path = f'testcase/{test_name}.out'
    
    llvm_path = f'tmp/{idx}.ll'
    exe_path = f'tmp/{idx}.exe'
    answer_path = f'tmp/{idx}.out'

    wa_path = f'wa/{idx}_{test_name.replace("/", "_")}.out'

    def run() -> (bool, str):
        ok, msg = source_to_llvm(source_path, llvm_path)
        if not ok: return ok, msg

        ok, msg = llvm_to_exe(llvm_path, exe_path)
        if not ok: return ok, msg

        ok, answer, return_code, msg = run_exe(exe_path, input_path, answer_path)
        if not ok: return ok, msg

        ok, msg = check_answer(answer, correct_path, return_code, wa_path)
        return ok, msg

    ok, msg = run()
    print(f'{BOLD}({idx}/{total}){END} {test_name}: {msg}')
    return ok

        

def cleanup():
    shutil.rmtree('tmp/', ignore_errors=True)


def init():
    if not os.path.exists('out/'):
        os.makedirs('out/')
    if not os.path.exists('wa/'):
        os.makedirs('wa/')
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