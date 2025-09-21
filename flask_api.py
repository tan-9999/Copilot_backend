from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import traceback  # Add this import
from main import process_ai_request
from git_manager import GitManager  # Add Git support


app = Flask(__name__)
CORS(app, origins=["https://copilot-frontend-gules.vercel.app", "http://localhost:5173"])


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "AI Coding Buddy API is running"}), 200


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        prompt = data.get('prompt')
        working_directory = data.get('working_directory', 'D:\\Hackathon\\calculator')
        verbose = data.get('verbose', False)
        
        print(f"Received request:")  # Debug print
        print(f"  Prompt: {prompt}")
        print(f"  Working Directory: {working_directory}")
        print(f"  Verbose: {verbose}")
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Check if it's a Git URL or local directory
        git_manager = GitManager()
        if git_manager.is_valid_git_url(working_directory):
            print("Git URL detected, will be processed by main.py")
        else:
            # Only validate local directories
            if not os.path.exists(working_directory):
                return jsonify({
                    "error": f"Working directory does not exist: {working_directory}"
                }), 400
        
        # Process the request
        result = process_ai_request(prompt, working_directory, verbose)
        print(f"Result: {result}")  # Debug print
        
        if result.get("success"):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"Exception in chat endpoint: {e}")  # Debug print
        print(f"Traceback: {traceback.format_exc()}")  # Full traceback
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/api/validate-directory', methods=['POST'])
def validate_directory():
    try:
        data = request.json
        directory = data.get('directory')
        
        if not directory:
            return jsonify({"valid": False, "error": "Directory path is required"}), 400
        
        # Check if it's a Git URL
        git_manager = GitManager()
        if git_manager.is_valid_git_url(directory):
            # Validate Git repository
            local_path, error = git_manager.clone_or_update_repo(directory)
            
            if error:
                return jsonify({"valid": False, "error": error}), 400
            
            repo_info = git_manager.get_repo_info(local_path)
            return jsonify({
                "valid": True,
                "directory": directory,
                "type": "git_repository",
                "local_path": local_path,
                **repo_info
            }), 200
        else:
            # Validate local directory
            if os.path.exists(directory) and os.path.isdir(directory):
                files = os.listdir(directory)
                return jsonify({
                    "valid": True,
                    "directory": directory,
                    "type": "local_directory",
                    "fileCount": len([f for f in files if os.path.isfile(os.path.join(directory, f))]),
                    "dirCount": len([f for f in files if os.path.isdir(os.path.join(directory, f))])
                }), 200
            else:
                return jsonify({"valid": False, "error": "Directory does not exist"}), 404
            
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500


@app.route('/api/validate-repo', methods=['POST'])
def validate_repo():
    """Validate if a Git repository URL is accessible"""
    try:
        data = request.json
        repo_url = data.get('repo_url')
        
        if not repo_url:
            return jsonify({"valid": False, "error": "Repository URL is required"}), 400
        
        git_manager = GitManager()
        
        if not git_manager.is_valid_git_url(repo_url):
            return jsonify({"valid": False, "error": "Invalid Git repository URL"}), 400
        
        # Try to clone (this will be cached)
        local_path, error = git_manager.clone_or_update_repo(repo_url)
        
        if error:
            return jsonify({"valid": False, "error": error}), 400
        
        repo_info = git_manager.get_repo_info(local_path)
        
        return jsonify({
            "valid": True,
            "repo_url": repo_url,
            "local_path": local_path,
            **repo_info
        }), 200
            
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500


if __name__ == '__main__':
    print("Starting AI Coding Buddy API on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
