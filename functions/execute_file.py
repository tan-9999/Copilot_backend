# import os
# import subprocess
# from google.genai import types


# def execute_file(working_directory: str, file_path: str, args = []):
#     abs_working_dir = os.path.abspath(working_directory)
#     abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    
#     if not abs_file_path.startswith(abs_working_dir):
#         return f'Error: "{file_path}" is not in a working directory'
    
#     if not os.path.isfile(abs_file_path):
#         return f'Error: "{file_path}" is not a file'
    
#     if not file_path.endswith(".py"):
#         return f'"{file_path}" is not a Python file.'
    
#     try:
#         final_args = ["python", file_path]
#         final_args.extend(args)
#         output = subprocess.run(
#             final_args,
#             cwd=abs_working_dir,
#             timeout=30,
#             capture_output=True
#         )
#         final_string = f"""
#         STDOUT: {output.stdout}
#         STDERR: {output.stderr}
#         """
#         if output.stdout == "" and output.stderr == "":
#             final_string = "No output produced."
        
#         if output.returncode != 0:
#             final_string += f"Process existed with code {output.returncode}"
        
#         return final_string
        
#     except Exception as e:
#         return f'Error: executing Python file: {e}'
    
    
# schema_execute_file = types.FunctionDeclaration(
#     name="execute_file",
#     description="Runs the python file with python interpreter. Accept additional CLI args as an optional Array.",
#     parameters=types.Schema(
#         type=types.Type.OBJECT,
#         properties={
#             "file_path": types.Schema(
#                 type=types.Type.STRING,
#                 description="File to run relative to the working directory.",
#             ),
#             "args": types.Schema(
#                 type=types.Type.ARRAY,
#                 description="An optional array of string to be used as CLI args for the python file.",
#                 items=types.Schema(
#                     type=types.Type.STRING
#                 )
#             ),
#         },
#     ),
# )



import os
import subprocess
from pathlib import Path
from typing import Sequence, Optional

# ────────────────────────────────────────────────────────────────
# Unified runner
# ────────────────────────────────────────────────────────────────
def execute_file(
    working_directory: str,
    file_path: str,
    args: Optional[Sequence[str]] = None,
) -> str:
    """
    Safely execute a source file located inside `working_directory`.

    Supported extensions
      • .py         → python …          (interpreted)
      • .js / .jsx  → node …           (interpreted)
      • .cpp        → g++ … && ./a.out (compiled, C++17)
      • .java       → javac … && java  (compiled)

    `args` (list[str]) is appended verbatim after the program name,
    so every language receives the same command-line arguments.
    """
    if args is None:
        args = []

    workdir = Path(working_directory).resolve()
    target  = (workdir / file_path).resolve()

    # ---------- security guard ----------
    if not target.is_file():
        return f'Error: "{file_path}" is not a file.'
    if workdir not in target.parents:
        return f'Error: "{file_path}" is outside the working directory.'

    ext = target.suffix.lower()
    cmd: list[str]  # final command we will run

    # ---------- dispatch by extension ----------
    if ext == ".py":
        cmd = ["python", str(target)]

    elif ext in (".js", ".jsx"):
        cmd = ["node", str(target)]

    elif ext == ".cpp":
        exe = target.with_suffix("")              # main.cpp → main
        comp = subprocess.run(
            ["g++", "-std=c++17", "-O2", "-o", str(exe), str(target)],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        if comp.returncode != 0:
            return f"C++ compilation failed:\n{comp.stderr}"
        cmd = [str(exe)]

    elif ext == ".java":
        comp = subprocess.run(
            ["javac", str(target)],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        if comp.returncode != 0:
            return f"Java compilation failed:\n{comp.stderr}"
        class_name = target.stem                 # HelloWorld.java → HelloWorld
        cmd = ["java", "-cp", str(workdir), class_name]

    else:
        return f'Error: unsupported file type "{ext}".'

    # attach user-provided CLI arguments
    cmd.extend(args)

    # ---------- run with 30 s timeout ----------
    try:
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            timeout=30,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return "Error: execution exceeded 30 s timeout."
    except FileNotFoundError as e:
        return f"Error: required interpreter or compiler not found: {e}"

    if not proc.stdout and not proc.stderr:
        return "No output produced."

    out =  f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    if proc.returncode != 0:
        out += f"\nProcess exited with code {proc.returncode}"
    return out


# ────────────────────────────────────────────────────────────────
# OPTIONAL: schema object (if you still expose this via genai)
# ────────────────────────────────────────────────────────────────
try:
    from google.genai import types  # only if the SDK is present

    schema_execute_file = types.FunctionDeclaration(
        name="execute_file",
        description=(
            "Runs a Python, JavaScript, C++ or Java file located inside the "
            "working directory. Accepts additional CLI args as an optional array."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "file_path": types.Schema(
                    type=types.Type.STRING,
                    description="File to run (relative to the working directory).",
                ),
                "args": types.Schema(
                    type=types.Type.ARRAY,
                    description="Optional list of CLI arguments.",
                    items=types.Schema(type=types.Type.STRING),
                ),
            },
        ),
    )

except ModuleNotFoundError:
    # Skip schema creation when google-genai is not available
    pass
