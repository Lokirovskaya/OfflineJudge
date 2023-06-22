########### Config Here ###########

SRC_DIR_PATH = 'aa.c'
COMPILE_TIMEOUT = 5
EXEC_TIMEOUT = 60

###################################

import os
import sys
import subprocess as sp
import shutil
import multiprocessing
import concurrent.futures as cf
from typing import Union, Optional


COMPILER_TARGET_PATH = 'out/compiler.exe'

RED = '\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BOLD = '\x1b[1m'
END = '\x1b[0m'

def get_tests_names():
    test_set = set()
    for root, dirs, files in os.walk('testcase/'):
        relative_path = os.path.relpath(root, 'testcase/')
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
        '-w',
    ]
    try:
        r = sp.run(args, timeout=COMPILE_TIMEOUT, stdout=sp.PIPE, stderr=sp.PIPE)
    except sp.TimeoutExpired:
        return (
            False,
            f'{YELLOW}{BOLD}Time Limit Exceeded{END}{YELLOW} when running your compiler ({COMPILE_TIMEOUT} s).{END}'
        )

    if r.returncode != 0:
        with open(kwargs['re_path'], 'wb') as re_file:
            re_file.write(r.stdout)
            re_file.write(r.stderr)
        return (
            False,
            f'{YELLOW}{BOLD}Runtime Error{END}{YELLOW} when running your compiler, stderr in {kwargs["re_path"]}{END}'
        )
    return (True, None)


def llvm_to_exe(llvm_path, exe_path, **kwargs) -> (bool, Optional[str]):
    args = [
        'clang',
        llvm_path,
        'lib/lib.o',
        '-o',
        exe_path,
        '-O0',
    ]
    r = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
    if r.returncode != 0:
        with open(kwargs['re_path'], 'wb') as re_file:
            re_file.write(r.stdout)
            re_file.write(r.stderr)
        return (
            False,
            f'{YELLOW}{BOLD}Runtime Error{END}{YELLOW} when compiling LLVM IR, stderr in {kwargs["re_path"]}{END}'
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
                return (True, r.stdout.decode('utf-8'), r.returncode % 256, None)
        # no stdin
        else:
            r = sp.run(args, stdout=sp.PIPE, stderr=sp.DEVNULL, timeout=EXEC_TIMEOUT)
            return (True, r.stdout.decode('utf-8'), r.returncode % 256, None)
    except sp.TimeoutExpired:
        return (
            False,
            None,
            None,
            f'{YELLOW}{BOLD}Time Limit Exceeded{END}{YELLOW} when running exe file ({EXEC_TIMEOUT} s).{END}'
        )


def check_ans(ans_str, correct_path, return_code, **kwargs) -> (bool, str):
    def dump_wa(wa_lines):
        with open(kwargs['wa_path'], 'w') as wa_file:
            for line in wa_lines:
                print(line, file=wa_file)
    def create_diff_bat():
        with open(kwargs['diff_path'], 'w') as diff_file:
            diff_file.write(f'code --diff ../{kwargs["wa_path"]} ../{correct_path}')
            
    with open(correct_path, 'r') as correct_file:
        # strip line ends and file end
        ans_lines = [line.rstrip() for line in ans_str.rstrip().splitlines()] 
        ans_lines.append(str(return_code))

        correct_str = correct_file.read()
        correct_lines = [line.rstrip() for line in correct_str.rstrip().splitlines()] 

        if len(ans_lines) != len(correct_lines):
            dump_wa(ans_lines)
            create_diff_bat()
            return (
                False,
                f'{RED}{BOLD}Wrong Answer{END}{RED}, run {kwargs["diff_path"]} for detail.{END}'
            )
            
        for i in range(len(ans_lines)):
            if ans_lines[i] != correct_lines[i]:
                dump_wa(ans_lines)
                create_diff_bat()
                return (
                    False,
                    f'{RED}{BOLD}Wrong Answer{END}{RED}, run {kwargs["diff_path"]} for detail.{END}'
                )
                
        return (True, f'{GREEN}{BOLD}Accepted.{END}')


def judge_one(test_name, idx) -> bool:
    input_path = f'testcase/{test_name}.in'
    source_path = f'testcase/{test_name}.sy'
    correct_path = f'testcase/{test_name}.out'
    
    llvm_path = f'tmp/{idx}.ll'
    exe_path = f'tmp/{idx}.exe'

    test_name_no_dash = test_name.replace('/', '_')
    wa_path = f'wa/wa_out/{idx}_WA_{test_name_no_dash}.out'
    diff_path = f'wa/{idx}_WA_{test_name_no_dash}_show_diff.bat'
    re_path = f'wa/{idx}_RE_{test_name_no_dash}.txt'

    def run() -> (bool, str):
        ok, msg = source_to_llvm(source_path, llvm_path, re_path=re_path)
        if not ok: return ok, msg

        ok, msg = llvm_to_exe(llvm_path, exe_path, re_path=re_path)
        if not ok: return ok, msg

        ok, ans, return_code, msg = run_exe(exe_path, input_path)
        if not ok: return ok, msg

        ok, msg = check_ans(ans, correct_path, return_code, wa_path=wa_path, diff_path=diff_path)
        return ok, msg

    ok, msg = run()
    if ok:
        print(f'{GREEN}{BOLD}AC{END} ', end='')
        sys.stdout.flush()
    else:
        print(f'\n{BOLD}({idx}){END} {test_name}: {msg}')
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
    

# return True means all AC
def main() -> bool:
    init()
    print(f'{BOLD}Compiling Java...{END}')
    compile_compiler()

    test_list = [(i + 1, test) for i, test in enumerate(get_tests_names())]
    print(f'{BOLD}Test start!{END} You can press Ctrl-C to cancel')

    num_cores = multiprocessing.cpu_count()
    print(f'{BOLD}Running{END} {YELLOW}{BOLD}{len(test_list)}{END} {BOLD}tests on{END} {YELLOW}{BOLD}{num_cores}{END} {BOLD}cores!{END}')
    
    executor = cf.ProcessPoolExecutor(max_workers=num_cores)
    futures = [executor.submit(judge_one, test_name, idx)
               for idx, test_name in test_list]
    
    result_list = []
    for future in cf.as_completed(futures):
        result = future.result()
        result_list.append(result)
        
    passed = result_list.count(True)
    total = len(result_list)
              
    print(f'\n{BOLD}Test Finished!{END} {GREEN}{BOLD}Accepted: ({passed}/{total}){END} {RED}{BOLD}Failed: ({total - passed}/{total}){END}')
    cleanup()
    input('Press Enter to Exit') # comment this line when CI/CD
    return passed == total

main()