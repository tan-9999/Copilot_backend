import os
from google.genai import types

# working_directory = r'D:\Hackathon\calculator'

def get_file(working_directory, directory="."):
    abs_working_dir = os.path.abspath(working_directory)
    abs_directory = os.path.abspath(os.path.join(working_directory, directory))
    
    if not abs_directory.startswith(abs_working_dir):
        return f'Error: "{directory}" is not in a working directory'
    
    final_responce = ""
    contents = os.listdir(abs_directory)
    for content in contents:
        content_path = os.path.join(abs_directory, content)
        is_dir = os.path.isdir(content_path)
        size = os.path.getsize(content_path)
        final_responce += f"- {content}: file_size={size} bytes, is_dir={is_dir} \n"
    return final_responce
    
# get_file(working_directory)

schema_get_file = types.FunctionDeclaration(
    name="get_file",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)