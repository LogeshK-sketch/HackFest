import os
import sys
import uuid
import time
import tempfile
import subprocess

RESTRICTED_KEYWORDS = [
    'import os', 'import sys', 'import subprocess', 'import socket',
    'import shutil', 'open(', '__import__', 'eval(', 'exec(', 'compile(',
    'globals(', 'locals(', 'getattr(', 'setattr(', 'delattr('
]

def run_code(code: str, stdin_input: str, expected_output: str = None, timeout: int = 2) -> dict:
    """
    Executes Python code in a child process safely.
    Checks against restricted keywords.
    Compares the generated stdout against expected_output if provided.
    """
    if len(code) > 10000:
        return {"status": "error", "output": "", "error": "Code length exceeds 10000 characters limit.", "execution_time": 0.0}

    for keyword in RESTRICTED_KEYWORDS:
        if keyword in code:
            return {"status": "error", "output": "", "error": "SecurityError: Use of restricted module/function.", "execution_time": 0.0}

    # Generate a unique temp file name using system temp dir
    run_id = str(uuid.uuid4())
    temp_dir = tempfile.gettempdir()
    
    code_file = os.path.join(temp_dir, f"user_code_{run_id}.py")
    input_file_path = os.path.join(temp_dir, f"user_input_{run_id}.txt")
    
    try:
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        with open(input_file_path, 'w', encoding='utf-8') as f:
            f.write(stdin_input or "")
            
        start_time = time.time()
        
        with open(input_file_path, 'r', encoding='utf-8') as inp:
            proc = subprocess.run(
                [sys.executable, code_file],
                stdin=inp,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
        execution_time = round(time.time() - start_time, 4)
        
        if proc.returncode != 0:
            return {
                "status": "error",
                "output": proc.stdout,
                "error": proc.stderr,
                "execution_time": execution_time
            }
            
        actual_output = proc.stdout.strip()
        
        status = "passed"
        if expected_output is not None:
             if actual_output != expected_output.strip():
                 status = "failed"
                 
        return {
            "status": status,
            "output": actual_output,
            "error": "",
            "execution_time": execution_time
        }
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "", "error": "TimeLimitExceeded: Code took too long.", "execution_time": float(timeout)}
    except Exception as e:
        return {"status": "error", "output": "", "error": f"ExecutionError: {str(e)}", "execution_time": 0.0}
    finally:
        # Cleanup temp files regardless of whether execution crashed or timed out
        if os.path.exists(code_file):
            try:
                os.remove(code_file)
            except:
                pass
        if os.path.exists(input_file_path):
            try:
                os.remove(input_file_path)
            except:
                pass
