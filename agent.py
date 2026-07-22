import subprocess
import ollama
import json
import sys
import os
from datetime import datetime

MAX_ATTEMPTS = 5
MODEL_NAME = 'llama3.2:3b'


def run_tests(test_file_path):
    """Runs pytest on the given test file path and returns (passed, output)."""
    test_dir = os.path.dirname(os.path.abspath(test_file_path))
    test_file_name = os.path.basename(test_file_path)

    result = subprocess.run(
        ['pytest', test_file_name, '-v'],
        cwd=test_dir,
        capture_output=True,
        text=True
    )
    passed = result.returncode == 0
    output = result.stdout + result.stderr
    return passed, output


def read_code(code_file_path):
    with open(code_file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_code(code_file_path, new_code):
    with open(code_file_path, 'w', encoding='utf-8') as f:
        f.write(new_code)


def ask_model_for_fix(code_file_name, code, error_output):
    prompt = f"""You are fixing a bug in a Python file called {code_file_name}.

Here is the current code:

{code}

Here is the pytest failure output when running its tests:

{error_output}

Fix the bug. Respond with ONLY the corrected full contents of {code_file_name}.
Do not include explanations, markdown formatting, or code fences. Just the raw Python code.
"""
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']


def clean_code_response(text):
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        lines = lines[1:]
        if lines and lines[-1].strip().startswith('```'):
            lines = lines[:-1]
        text = '\n'.join(lines)
    return text.strip()


def heal(code_file_path, test_file_path, log_dir='logs', on_attempt=None):
    """
    Runs the self-healing loop on any code file + test file, given as full or relative paths.

    on_attempt: optional callback function called after each attempt with the attempt_record dict.
                Useful for streaming progress to a UI instead of just printing.
    """
    code_file_path = os.path.abspath(code_file_path)
    test_file_path = os.path.abspath(test_file_path)
    code_file_name = os.path.basename(code_file_path)

    original_code = read_code(code_file_path)
    trail = []
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print("")
        print("=" * 50)
        print(f"[{code_file_name}] ATTEMPT {attempt}")
        print("=" * 50)

        passed, output = run_tests(test_file_path)

        attempt_record = {
            'attempt': attempt,
            'test_output': output,
            'passed': passed,
        }

        if passed:
            print(f"PASSED on attempt {attempt}!")
            attempt_record['note'] = 'Success - no fix needed this round.'
            trail.append(attempt_record)
            if on_attempt:
                on_attempt(attempt_record)
            save_log(code_file_name, run_id, trail, 'success', attempt, log_dir)
            print("")
            print("Final working code:")
            print(read_code(code_file_path))
            return {'success': True, 'attempts': attempt, 'final_code': read_code(code_file_path), 'trail': trail}

        print(f"FAILED. Error:\n{output}")
        print("")
        print("--- Asking model for a fix ---")
        print("")

        code_before = read_code(code_file_path)
        fix = ask_model_for_fix(code_file_name, code_before, output)
        fix = clean_code_response(fix)

        print("Model's proposed fix:")
        print(fix)

        attempt_record['code_before'] = code_before
        attempt_record['proposed_fix'] = fix
        trail.append(attempt_record)
        if on_attempt:
            on_attempt(attempt_record)

        write_code(code_file_path, fix)

    print(f"Reached max attempts ({MAX_ATTEMPTS}) without passing.")
    print("Restoring original broken code for reference.")
    write_code(code_file_path, original_code)
    save_log(code_file_name, run_id, trail, 'gave_up', MAX_ATTEMPTS, log_dir)
    return {'success': False, 'attempts': MAX_ATTEMPTS, 'final_code': original_code, 'trail': trail}


def save_log(code_file_name, run_id, trail, final_status, final_attempt, log_dir='logs'):
    log_data = {
        'code_file': code_file_name,
        'run_id': run_id,
        'final_status': final_status,
        'final_attempt': final_attempt,
        'attempts': trail,
    }
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{code_file_name.replace('.py', '')}_{run_id}.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    print(f"Full reasoning trail saved to {log_path}")


if __name__ == '__main__':
    if len(sys.argv) == 3:
        # Run on any specified file pair, e.g.:
        # python agent.py C:\path\to\my_file.py C:\path\to\test_my_file.py
        heal(sys.argv[1], sys.argv[2])
    else:
        print("No file specified - running on all known demo bugs.")
        heal('broken_code/calculator.py', 'broken_code/test_calculator.py')
        heal('broken_code/string_utils.py', 'broken_code/test_string_utils.py')
        heal('broken_code/inventory.py', 'broken_code/test_inventory.py')