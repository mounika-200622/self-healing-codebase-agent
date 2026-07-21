import subprocess
import ollama
import json
import sys
from datetime import datetime

MAX_ATTEMPTS = 5


def run_tests(test_file):
    result = subprocess.run(
        ['pytest', test_file, '-v'],
        cwd='broken_code',
        capture_output=True,
        text=True
    )
    passed = result.returncode == 0
    output = result.stdout + result.stderr
    return passed, output


def read_code(code_file):
    with open(f'broken_code/{code_file}', 'r', encoding='utf-8') as f:
        return f.read()


def write_code(code_file, new_code):
    with open(f'broken_code/{code_file}', 'w', encoding='utf-8') as f:
        f.write(new_code)


def ask_model_for_fix(code_file, code, error_output):
    prompt = f"""You are fixing a bug in a Python file called {code_file}.

Here is the current code:

{code}

Here is the pytest failure output when running its tests:

{error_output}

Fix the bug. Respond with ONLY the corrected full contents of {code_file}.
Do not include explanations, markdown formatting, or code fences. Just the raw Python code.
"""
    response = ollama.chat(model='llama3.2:3b', messages=[
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


def heal(code_file, test_file):
    original_code = read_code(code_file)
    trail = []
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print("")
        print("=" * 50)
        print(f"[{code_file}] ATTEMPT {attempt}")
        print("=" * 50)

        passed, output = run_tests(test_file)

        attempt_record = {
            'attempt': attempt,
            'test_output': output,
            'passed': passed,
        }

        if passed:
            print(f"PASSED on attempt {attempt}!")
            attempt_record['note'] = 'Success - no fix needed this round.'
            trail.append(attempt_record)
            save_log(code_file, run_id, trail, final_status='success', final_attempt=attempt)
            print("")
            print("Final working code:")
            print(read_code(code_file))
            return True

        print(f"FAILED. Error:\n{output}")
        print("")
        print("--- Asking model for a fix ---")
        print("")

        code_before = read_code(code_file)
        fix = ask_model_for_fix(code_file, code_before, output)
        fix = clean_code_response(fix)

        print("Model's proposed fix:")
        print(fix)

        attempt_record['code_before'] = code_before
        attempt_record['proposed_fix'] = fix
        trail.append(attempt_record)

        write_code(code_file, fix)

    print(f"Reached max attempts ({MAX_ATTEMPTS}) without passing.")
    print("Restoring original broken code for reference.")
    write_code(code_file, original_code)
    save_log(code_file, run_id, trail, final_status='gave_up', final_attempt=MAX_ATTEMPTS)
    return False


def save_log(code_file, run_id, trail, final_status, final_attempt):
    log_data = {
        'code_file': code_file,
        'run_id': run_id,
        'final_status': final_status,
        'final_attempt': final_attempt,
        'attempts': trail,
    }
    log_path = f'logs/{code_file.replace(".py", "")}_{run_id}.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    print(f"Full reasoning trail saved to {log_path}")


if __name__ == '__main__':
    if len(sys.argv) == 3:
        heal(sys.argv[1], sys.argv[2])
    else:
        print("No file specified - running on all known bugs.")
        heal('calculator.py', 'test_calculator.py')
        heal('string_utils.py', 'test_string_utils.py')
        heal('inventory.py', 'test_inventory.py')


        