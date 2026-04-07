import subprocess
import os
import sys

def run_script(path):
    if not os.path.exists(path):
        return {"error": "Script not found"}
    
    try:
        # Run with timeout to prevent hangs
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Execution timed out"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import json
        print(json.dumps(run_script(sys.argv[1])))
