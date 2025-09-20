import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
# Functions:
from functions.get_file import schema_get_file
from functions.read_file import schema_read_file
from functions.execute_file import schema_execute_file
# Func. call
from call_function import call_function

def process_ai_request(prompt, working_directory, verbose_flag=False):
    """
    Modified main function to accept working_directory and return results
    """
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

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
    
    # Create model with tools
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_prompt,
        tools=[schema_get_file, schema_read_file, schema_execute_file]
    )
    
    max_iters = 20
    function_calls_made = []
    chat_history = [{"role": "user", "parts": [prompt]}]
    
    for i in range(max_iters):
        try:
            response = model.generate_content(chat_history)
            
            if response is None:
                return {"error": "Response is malformed"}
            
            # Get token info if available
            token_info = {}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_info = {
                    'prompt_tokens': response.usage_metadata.prompt_token_count,
                    'response_tokens': response.usage_metadata.candidates_token_count
                }
            
            if verbose_flag and token_info:
                print(f"User prompt: {prompt}")
                print(f"Prompt token: {token_info.get('prompt_tokens', 0)}")
                print(f"Response token: {token_info.get('response_tokens', 0)}")
            
            # Check for function calls
            has_function_calls = False
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        function_call = part.function_call
                        
                        # Track function calls for frontend
                        function_calls_made.append({
                            'name': function_call.name,
                            'args': dict(function_call.args) if function_call.args else {}
                        })
                        
                        # Execute function
                        result = call_function(function_call, working_directory, verbose_flag)
                        
                        # Add function result to chat history
                        chat_history.append({
                            "role": "model", 
                            "parts": [part]
                        })
                        chat_history.append({
                            "role": "function",
                            "parts": [{
                                "function_response": {
                                    "name": function_call.name,
                                    "response": {"result": result}
                                }
                            }]
                        })
            
            if not has_function_calls:
                # Final response
                return {
                    "success": True,
                    "finalResponse": response.text,
                    "tokenCounts": token_info if verbose_flag else None,
                    "totalIterations": i + 1,
                    "functionCalls": function_calls_made,
                    "workingDirectory": working_directory
                }
                
        except Exception as e:
            return {"error": f"Error in iteration {i}: {str(e)}"}
    
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
