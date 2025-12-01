# bffpp.py

import sys
import importlib.util
import os

loaded_files = set()

def load_bf_file(path):
    """Load a .bf file, handle nested imports, and return its contents."""
    global loaded_files

    path = os.path.abspath(path)

    # Avoid re-importing the same file
    if path in loaded_files:
        return ""

    loaded_files.add(path)

    with open(path, "r") as f:
        text = f.read()

    lines = text.splitlines()
    output = []

    for line in lines:
        line = line.strip()

        if line.startswith("#import"):
            # Parse import syntax #import "filename"
            start = line.find('"') + 1
            end = line.rfind('"')
            file_path = line[start:end]

            # Resolve relative to current file directory
            dirpath = os.path.dirname(path)
            file_path = os.path.join(dirpath, file_path)

            # Recursively load imported file
            imported_code = load_bf_file(file_path)
            output.append(imported_code)
        else:
            output.append(line)

    return "\n".join(output)


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
        elif cmd == '&':
            pc += 1
            
            # === Parse function name ===
            start = pc
            while pc < code_len and (code[pc].isalnum() or code[pc] in "_"):
                pc += 1
            func_name = code[start:pc]
            
            # Skip whitespace
            while pc < code_len and code[pc].isspace():
                pc += 1

            # === Parse a list of integer arguments ===
            args = []
            while pc < code_len:
                # If not a digit, stop parsing arguments
                if not code[pc].isdigit():
                    break
                
                # Parse multi-digit integer
                arg_start = pc
                while pc < code_len and code[pc].isdigit():
                    pc += 1
                args.append(int(code[arg_start:pc]))

                # Skip whitespace before next argument
                while pc < code_len and code[pc].isspace():
                    pc += 1

            # Call the external function
            call_external(memory, func_name, args)

            # Adjust because main loop will increment pc
            pc -= 1


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