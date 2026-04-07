# SOP: Coding Assistant

## Goal
Autonomously write and test utility scripts to improve the user's environment.

## Inputs
- `task_description`: The problem to solve.

## Process
1. Use the Brain to generate Python code for the `task_description`.
2. Save the code to a unique filename in `.tmp/autonomous_scripts/`.
3. Run `execution/run_autonomous_script.py` with the path to the new script.
4. Capture the stdout/stderr.
5. If successful:
    - Inform the user that the tool is ready.
6. If failed:
    - Use the Brain to analyze the error and attempt one retry.

## Outputs
- `script_path`: Path to the generated script.
- `execution_result`: "Success" or "Failure".
- `output`: Resulting data/logs.
