from functions.get_file import get_file
from functions.read_file import read_file
from functions.execute_file import execute_file

def call_function(function_call_part, working_directory, verbose=False):
    try:
        if verbose:
            print(f" - Calling function: {function_call_part.name}({function_call_part.args})")
        else:
            print(f" - Calling function: {function_call_part.name}")
            
        function_name = function_call_part.name
        function_args = dict(function_call_part.args) if function_call_part.args else {}
        
        if function_name == "get_file":
            result = get_file(working_directory, **function_args)
        elif function_name == "read_file":
            result = read_file(working_directory, **function_args)
        elif function_name == "execute_file":
            result = execute_file(working_directory, **function_args)
        else:
            return f"Error: Unknown function: {function_name}"
        
        return result
        
    except Exception as e:
        print(f"Error in call_function: {e}")
        return f"Error calling {function_call_part.name}: {str(e)}"


# from functions.get_file import get_file
# from functions.read_file import read_file
# from functions.execute_file import execute_file
# from google.genai import types

# working_directory = r'D:\Hackathon\calculator'

# def call_function(function_call_part, verbose=False):
#     if verbose:
#         print(f" - Calling function: {function_call_part.name}({function_call_part.args})")
#     else:
#         print(f" - Calling function: {function_call_part.name}")
        
#     result = ""
#     if function_call_part.name == "get_file":
#         result = get_file(working_directory, **function_call_part.args)
#     if function_call_part.name == "read_file":
#         result = read_file(working_directory, **function_call_part.args)
#     if function_call_part.name == "execute_file":
#         result = execute_file(working_directory, **function_call_part.args)
#     if result == "":   
#         return types.Content(
#             role="tool",
#             parts=[
#                 types.Part.from_function_response(
#                     name=function_call_part.name,
#                     response={"error":f"Unkown function: {function_call_part.name}"},
#                 )
#             ],
#         )
#     return types.Content(
#             role="tool",
#             parts=[
#                 types.Part.from_function_response(
#                     name=function_call_part.name,
#                     response={"result": result},
#                 )
#             ],
#         )