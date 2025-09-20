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
    try:
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
        
        for i in range(max_iters):
            try:
                print(f"Iteration {i+1}: Sending prompt to model")
                
                response = model.generate_content(prompt)
                
                print(f"Response received, checking for function calls...")
                
                if not response.candidates:
                    return {"error": "No response candidates received"}
                
                # Check for function calls in the response
                has_function_calls = False
                
                for candidate in response.candidates:
                    if not candidate.content or not candidate.content.parts:
                        continue
                        
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            has_function_calls = True
                            function_call = part.function_call
                            
                            print(f"Function call detected: {function_call.name}")
                            
                            # Track function calls for frontend
                            function_calls_made.append({
                                'name': function_call.name,
                                'args': dict(function_call.args) if function_call.args else {}
                            })
                            
                            # Execute function with working_directory
                            result = call_function(function_call, working_directory, verbose_flag)
                            print(f"Function result: {result}")
                            
                            # Create new chat with function result
                            prompt = f"Previous function call {function_call.name} returned: {result}\nPlease continue with the original request."
                
                # If no function calls, this is the final response
                if not has_function_calls:
                    print("No function calls detected, returning final response")
                    return {
                        "success": True,
                        "finalResponse": response.text if response.text else "No response text",
                        "tokenCounts": {
                            'prompt_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0,
                            'response_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0
                        } if verbose_flag else None,
                        "totalIterations": i + 1,
                        "functionCalls": function_calls_made,
                        "workingDirectory": working_directory
                    }
                    
            except Exception as e:
                print(f"Error in iteration {i}: {e}")
                return {"error": f"Error in iteration {i}: {str(e)}"}
        
        return {
            "error": "Maximum iterations reached",
            "functionCalls": function_calls_made,
            "totalIterations": max_iters
        }
        
    except Exception as e:
        print(f"Error in process_ai_request: {e}")
        return {"error": f"Error in process_ai_request: {str(e)}"}

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
