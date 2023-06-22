########### Config Here ###########

SRC_DIR_PATH = 'aa.c'
COMPILE_TIMEOUT = 5
EXEC_TIMEOUT = 60

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


def source_to_llvm(source_path, llvm_path, **kwargs) -> (bool, Optional[str]):
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
        r = sp.run(args, timeout=COMPILE_TIMEOUT, stdout=sp.DEVNULL, stderr=sp.PIPE)
    except sp.TimeoutExpired:
        return (
            False,
            f'{YELLOW}{BOLD}Time Limit Exceeded{END}{YELLOW}: Running Source -> LLVM IR ({COMPILE_TIMEOUT} s){END}'
        )

    if r.returncode != 0:
        with open(kwargs[re_path], 'w') as re_file:
            re_file.write(r.stderr.decode('utf-8'))
        return (
            False,
            f'{YELLOW}{BOLD}Runtime Error{END}{YELLOW}: Source -> LLVM IR{END}'
        )
    return (True, None)


def llvm_to_exe(llvm_path, exe_path, **kwargs) -> (bool, Optional[str]):
    args = [
        'clang',
        llvm_path,
        'lib/lib.o',
        '-o',
        exe_path,
        '-O0'
    ]
    r = sp.run(args, stdout=sp.DEVNULL, stderr=sp.PIPE)
    if r.returncode != 0:
        with open(kwargs[re_path], 'w') as re_file:
            re_file.write(r.stderr.decode('utf-8'))
        return (
            False,
            f'{YELLOW}{BOLD}Runtime Error{END}{YELLOW}: LLVM IR -> ASM{END}'
        )
    return (True, None)


# return: status, stdout, returncode, tle_msg 
def run_exe(exe_path, input_path, **kwargs) -> (bool, Optional[str], Optional[int], Optional[str]):
    args = ['./' + exe_path]
    try:
        # stdin available
        if os.path.exists(input_path):
            with open(input_path, 'r') as input_file:
                r = sp.run(args, stdin=input_file, stdout=sp.PIPE, stderr=sp.DEVNULL, timeout=EXEC_TIMEOUT)
                return (True, r.stdout.decode('utf-8'), r.returncode, None)
        # no stdin
        else:
            r = sp.run(args, stdout=sp.PIPE, stderr=sp.DEVNULL, timeout=EXEC_TIMEOUT)
            return (True, r.stdout.decode('utf-8'), r.returncode, None)
    except sp.TimeoutExpired:
        return (
            False,
            None,
            None,
            f'{YELLOW}{BOLD}Time Limit Exceeded{END}{YELLOW}: Running ASM ({EXEC_TIMEOUT} s){END}'
        )


def check_answer(answer_str, correct_path, return_code, **kwargs) -> (bool, str):
    def dump_wa(wa_lines):
        with open(kwargs[wa_path], 'w') as wa_file:
            wa_file.writelines(wa_lines)
    def create_diff_bat():
        with open(kwargs[diff_path], 'w') as diff_file:
            diff_file.write(f'code --diff ../{kwargs[wa_path]} ../{correct_path}')
            
    with open(correct_path, 'r') as correct_file:
        # strip line ends and file end
        ans_lines = [line.rstrip() for line in answer_str.rstrip().splitlines()] 
        ans_lines.append(str(return_code))

        correct_str = correct_file.read()
        correct_lines = [line.rstrip() for line in correct_str.rstrip().splitlines()] 

        if len(ans_lines) != len(correct_lines):
            dump_wa(ans_lines)
            create_diff_bat()
            return (
                False,
                f'{RED}{BOLD}Wrong Answer{END}'
            )
            
        for i in range(len(ans_lines)):
            if ans_lines[i] != correct_lines[i]:
                dump_wa(ans_lines)
                create_diff_bat()
                return (
                    False,
                    f'{RED}{BOLD}Wrong Answer{END}'
                )
                
        return (True, f'{GREEN}{BOLD}Accepted{END}')


def judge_one(test_name, idx, total) -> bool:
    input_path = f'testcase/{test_name}.in'
    source_path = f'testcase/{test_name}.sy'
    correct_path = f'testcase/{test_name}.out'
    
    llvm_path = f'tmp/{idx}.ll'
    exe_path = f'tmp/{idx}.exe'

    wa_path = f'wa/wa_out/{idx}_WA_{test_name.replace("/", "_")}.out'
    diff_path = f'wa/{idx}_WA_show_diff.bat'
    re_path = f'wa/{idx}_RE_{test_name.replace("/", "_")}.txt'

    def run() -> (bool, str):
        ok, msg = source_to_llvm(source_path, llvm_path, re_path=re_path)
        if not ok: return ok, msg

        ok, msg = llvm_to_exe(llvm_path, exe_path, re_path=re_path)
        if not ok: return ok, msg

        ok, answer, return_code, msg = run_exe(exe_path, input_path)
        if not ok: return ok, msg

        ok, msg = check_answer(answer, correct_path, return_code, wa_path=wa_path, diff_path=diff_path)
        return ok, msg

    ok, msg = run()
    print(f'{BOLD}({idx}/{total}){END} {test_name}: {msg}')
    return ok

        

def cleanup():
    shutil.rmtree('tmp/', ignore_errors=True)


def init():
    def mkdir(dir_path):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    def mkdir_empty(dir_path):
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path)
        
    mkdir('out')
    mkdir_empty('tmp')
    mkdir_empty('wa')
    mkdir('wa/wa_out')

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
    total = len(result_list)
              
    print(f'\n{BOLD}Test Finished!{END} {GREEN}{BOLD}Accepted: ({passed}/{total}){END} {RED}{BOLD}Failed: ({total - passed}/{total}){END}')
    cleanup()
    input('Press Enter to Exit')