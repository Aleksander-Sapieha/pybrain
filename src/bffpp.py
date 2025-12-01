# bffpp.py

import sys
import os
import importlib.util

external_functions = {}

def load_plugins(folder="python"):
    for file in os.listdir(folder):
        if file.endswith(".py"):
            path = os.path.join(folder, file)
            spec = importlib.util.spec_from_file_location(file[:-3], path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Register all functions from the plugin module
            for name in dir(module):
                if callable(getattr(module, name)):
                    external_functions[name] = getattr(module, name)

def call_external(mem, func_name, args):
    if func_name in external_functions:
        return external_functions[func_name](mem, args)
    else:
        raise Exception(f"External function '{func_name}' not found")

def brainfuck_interpreter(code, input_func=input, output_func=print):
    memory = [0] * 30000
    ptr = 0
    pc = 0
    code_len = len(code)

    # Precompute matching brackets
    brackets = {}
    stack = []
    for i, c in enumerate(code):
        if c == '[':
            stack.append(i)
        elif c == ']':
            start = stack.pop()
            brackets[start] = i
            brackets[i] = start

    # Find function definitions
    functions = {}  # func_id -> (start, end)
    i = 0
    while i < code_len:
        if code[i] == ':':
            i += 1
            func_id = int(code[i])
            func_start = i + 1
            func_end = code.find(':', func_start)
            if func_end == -1:
                raise Exception(f"Function :{func_id} not closed with ':'")
            functions[func_id] = (func_start, func_end)
            i = func_end
        i += 1

    call_stack = []

    while pc < code_len:
        cmd = code[pc]

        if cmd == '>':
            ptr += 1
        elif cmd == '<':
            ptr -= 1
        elif cmd == '+':
            memory[ptr] = (memory[ptr] + 1) % 256
        elif cmd == '-':
            memory[ptr] = (memory[ptr] - 1) % 256
        elif cmd == '.':
            output_func(chr(memory[ptr]), end='')
        elif cmd == ',':
            memory[ptr] = ord(input_func()[0])
        elif cmd == '[' and memory[ptr] == 0:
            pc = brackets[pc]
        elif cmd == ']' and memory[ptr] != 0:
            pc = brackets[pc]
        elif cmd == '@':  # Call function
            pc += 1
            func_id = int(code[pc])
            if func_id not in functions:
                raise Exception(f"Function :{func_id} not defined")
            func_start, func_end = functions[func_id]
            call_stack.append(pc)  # Return address
            pc = func_start - 1
        elif cmd == ':' and pc in [start for start, end in functions.values()]:
            # Skip function body if not called
            end = [end for start, end in functions.values() if start == pc+1][0]
            pc = end
        elif cmd == '&':  # Call external function
            # Read function name and arguments from code
            pc += 1
            start = pc
            while pc < code_len and code[pc].isalnum():
                pc += 1
            func_name = code[start:pc]

            # Skip space(s)
            while pc < code_len and code[pc] == ' ':
                pc += 1

            # Read argument cell indices
            args = []
            while pc < code_len and code[pc].isdigit():
                arg_start = pc
                while pc < code_len and code[pc].isdigit():
                    pc += 1
                args.append(int(code[arg_start:pc]))
                while pc < code_len and code[pc] == ' ':
                    pc += 1
            call_external(memory, func_name, args)
            pc -= 1  # Adjust for main loop increment

        pc += 1

        # Return from function
        if pc >= code_len and call_stack:
            pc = call_stack.pop() + 1




file = sys.argv[1]

if(file):
    with open(file) as bfpp_code:
        load_plugins()
        brainfuck_interpreter(bfpp_code)
    

else:
    print("Usage: bffpp [filename]")