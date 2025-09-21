import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
# Functions:
from functions.get_file import schema_get_file
from functions.read_file import schema_read_file
from functions.execute_file import schema_execute_file
# Func. call
from call_function import call_function
# Git support
from git_manager import GitManager


def process_ai_request(prompt, working_directory, verbose_flag=False):
    """
    Modified main function to accept working_directory and return results
    """
    # Git repository support
    git_manager = GitManager()
    original_directory = working_directory
    repo_info = None
    
    if git_manager.is_valid_git_url(working_directory):
        print(f"Git URL detected: {working_directory}")
        local_path, error = git_manager.clone_or_update_repo(working_directory)
        if error:
            return {"error": f"Git operation failed: {error}"}
        working_directory = local_path
        repo_info = git_manager.get_repo_info(local_path)
    
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)


    system_prompt = """
            You are a helpful AI coding agent.


            When a user asks a question or makes a request, make a function call plan. You can perform the following operations:


            - List files and directories
            - Read file contents
            - Execute Python files with optional arguments


            Note:
            -All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
            -When returning code, show code well formatted
        """
        
    messages = [
        types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        ),
    ]
    
    available_functions = types.Tool(
        function_declarations=[
            schema_get_file,
            schema_read_file,
            schema_execute_file,
        ] 
    )


    config=types.GenerateContentConfig(
        tools=[available_functions], 
        system_instruction=system_prompt
    )
    
    max_iters = 20
    function_calls_made = []
    
    for i in range(0, max_iters):
        
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
        config=config
        )
        
        if response is None or response.usage_metadata is None:
            return {"error": "Response is malformed"}
        
        token_info = {
            'prompt_tokens': response.usage_metadata.prompt_token_count,
            'response_tokens': response.usage_metadata.candidates_token_count
        }
        
        if verbose_flag:
            print(f"User prompt: {prompt}")
            print(f"Prompt token: {token_info['prompt_tokens']}")
            print(f"Response token: {token_info['response_tokens']}")
        
        if response.candidates:
            for candidate in response.candidates:
                if candidate is None or candidate.content is None:
                    continue
                messages.append(candidate.content)
        
        if response.function_calls:
            for function_call_part in response.function_calls:
                # Track function calls for frontend
                function_calls_made.append({
                    'name': function_call_part.name,
                    'args': dict(function_call_part.args) if function_call_part.args else {}
                })
                
                # Pass working_directory to call_function
                result = call_function(function_call_part, working_directory, verbose_flag)
                messages.append(result)
        else:
            # final message - return comprehensive response
            return {
                "success": True,
                "finalResponse": response.text,
                "tokenCounts": token_info if verbose_flag else None,
                "totalIterations": i + 1,
                "functionCalls": function_calls_made,
                "workingDirectory": original_directory,
                "repositoryInfo": repo_info
            }
    
    return {
        "error": "Maximum iterations reached",
        "functionCalls": function_calls_made,
        "totalIterations": max_iters
    }


def main():
    # Original command line interface (for backwards compatibility)
    if len(sys.argv) < 2:
        print("Prompt is too small!")
        sys.exit(1)
        
    verbose_flag = False
    working_directory = r'D:\Hackathon\calculator'  # Default
    
    if len(sys.argv) == 3 and sys.argv[2] == "--verbose":
        verbose_flag = True
    if len(sys.argv) == 4:  # Allow working directory as 3rd argument
        working_directory = sys.argv[3]
        
    prompt = sys.argv[1]
    
    result = process_ai_request(prompt, working_directory, verbose_flag)
    
    if result.get("success"):
        print(result["finalResponse"])
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
