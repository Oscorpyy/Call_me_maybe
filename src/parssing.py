import sys
import os
import json
import stat


def parse_and_validate_args() -> tuple[str, str, str]:
    """Manually parse sys.argv to extract file paths.
    Handles arguments in any order.

    Returns:
        tuple[str, str, str]: A tuple containing the paths to
        the input file, the output file, and the definition file.
    """
    # 1. Set default values
    config = {
        "--input": "data/input/function_calling_tests.json",
        "--output": "data/output/function_calling_results.json",
        "--functions_definition": "data/input/functions_definition.json"
    }

    # 2. Retrieve command-line arguments
    # sys.argv usually contains the script or module name
    args = sys.argv[1:]

    # 3. Iterate through the list looking for our flags
    i = 0
    while i < len(args):
        current_arg = args[i]

        if current_arg in config:
            if i + 1 < len(args):
                config[current_arg] = args[i + 1]
                i += 2
            else:
                print(f"❌ Error: Missing value for '{current_arg}'.")
                print("Expected usage:\n  uv run python -m src"
                      " [--input <file>] [--output <file>]"
                      " [--functions_definition <file>]")
                sys.exit(1)
        else:
            print(f"❌ Error: Unrecognized argument '{current_arg}'.")
            print("Expected usage:\n  uv run python -m src [--input <file>]"
                  " [--output <file>] [--functions_definition <file>]")
            sys.exit(1)

    # 4. Extract for clarity
    input_file = config["--input"]
    output_file = config["--output"]
    def_file = config["--functions_definition"]

    # --- File validation ---

    # Check if input file exists and is accessible
    if not os.path.isfile(input_file):
        print(f"❌ Critical error: Input file '{input_file}' not found.")
        sys.exit(1)

    input_stat = os.stat(input_file)
    if not bool(input_stat.st_mode & stat.S_IRUSR):
        print(f"❌ Critical error: No read permission for '{input_file}'.")
        sys.exit(1)

    if not os.access(input_file, os.R_OK):
        print(f"❌ Critical error: No read permission for '{input_file}'.")
        sys.exit(1)
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print(f"❌ Critical error: '{input_file}' is empty.")
                sys.exit(1)
            data = json.loads(content)
            if not isinstance(data, list):
                print(f"❌ Critical error: '{input_file}' must "
                      f"contain a JSON list.")
                sys.exit(1)
            if len(data) == 0:
                print(f"❌ Critical error: '{input_file}' is empty.")
                sys.exit(1)
            for item in data:
                if not isinstance(item, dict):
                    print(f"❌ Critical error: '{input_file}' items "
                          f"must be objects.")
                    sys.exit(1)
                if "prompt" not in item:
                    print(f"❌ Critical error: '{input_file}' missing "
                          f"'prompt' key.")
                    sys.exit(1)
                if not isinstance(item["prompt"], str):
                    print(f"❌ Critical error: '{input_file}' 'prompt' "
                          f"must be a string.")
                    sys.exit(1)
                if not item["prompt"].strip():
                    print(f"❌ Critical error: '{input_file}' 'prompt' "
                          f"cannot be empty.")
                    sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Critical error: '{input_file}' is not valid JSON. ({e})")
        sys.exit(1)
    except PermissionError:
        print(f"❌ Critical error: Permission denied to read '{input_file}'.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Critical error: Could not read '{input_file}'. ({e})")
        sys.exit(1)

    # Check if definitions file exists and is accessible
    if not os.path.isfile(def_file):
        print(f"❌ Critical error: Definitions file '{def_file}' not found.")
        sys.exit(1)

    def_stat = os.stat(def_file)
    if not bool(def_stat.st_mode & stat.S_IRUSR):
        print(f"❌ Critical error: No read permission for '{def_file}'.")
        sys.exit(1)

    if not os.access(def_file, os.R_OK):
        print(f"❌ Critical error: No read permission for '{def_file}'.")
        sys.exit(1)
    try:
        with open(def_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print(f"❌ Critical error: '{def_file}' is empty.")
                sys.exit(1)
            data = json.loads(content)
            if not isinstance(data, list):
                print(f"❌ Critical error: '{def_file}' must "
                      f"contain a JSON list.")
                sys.exit(1)
            if len(data) == 0:
                print(f"❌ Critical error: '{def_file}' is empty.")
                sys.exit(1)
            if data and not isinstance(data[0], dict):
                print(f"❌ Critical error: '{def_file}' must "
                      f"contain a list of objects.")
                sys.exit(1)
            valid_types = {"number", "integer", "boolean", "string"}
            for item in data:
                if not isinstance(item, dict):
                    print(f"❌ Critical error: '{def_file}' items must "
                          f"be objects.")
                    sys.exit(1)
                if "name" not in item or not isinstance(item["name"], str):
                    print(f"❌ Critical error: '{def_file}' missing or "
                          f"invalid 'name'.")
                    sys.exit(1)
                if not item["name"].strip():
                    print(f"❌ Critical error: '{def_file}' 'name' "
                          f"cannot be empty.")
                    sys.exit(1)
                if "description" not in item or not isinstance(
                        item["description"], str):
                    print(f"❌ Critical error: '{def_file}' missing or "
                          f"invalid 'description'.")
                    sys.exit(1)
                if not item["description"].strip():
                    print(f"❌ Critical error: '{def_file}' "
                          f"'description' cannot be empty.")
                    sys.exit(1)

                if "parameters" not in item:
                    print(f"❌ Critical error: '{def_file}' missing "
                          f"'parameters'.")
                    sys.exit(1)
                if not isinstance(item["parameters"], dict):
                    print(f"❌ Critical error: '{def_file}' "
                          f"'parameters' must be an object.")
                    sys.exit(1)
                for p_key, p_val in item["parameters"].items():
                    if not isinstance(p_val, dict) or "type" not in p_val:
                        print(f"❌ Critical error: '{def_file}' "
                              f"parameter '{p_key}' missing 'type'.")
                        sys.exit(1)
                    if p_val["type"] not in valid_types:
                        print(f"❌ Critical error: '{def_file}' "
                              f"invalid type '{p_val['type']}' in "
                              f"parameter '{p_key}'.")
                        sys.exit(1)

                if "returns" not in item:
                    print(f"❌ Critical error: '{def_file}' missing "
                          f"'returns'.")
                    sys.exit(1)
                ret_val = item["returns"]
                if not isinstance(ret_val, dict) or "type" not in ret_val:
                    print(f"❌ Critical error: '{def_file}' 'returns' "
                          f"must be an object containing 'type'.")
                    sys.exit(1)
                if ret_val["type"] not in valid_types:
                    print(f"❌ Critical error: '{def_file}' invalid "
                          f"returns type '{ret_val['type']}'.")
                    sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Critical error: '{def_file}' is not valid JSON. ({e})")
        sys.exit(1)
    except PermissionError:
        print(f"❌ Critical error: Permission denied to read '{def_file}'.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Critical error: Could not read '{def_file}'. ({e})")
        sys.exit(1)

    # Ensure output file parent directory exists and is writable
    output_dir = os.path.dirname(output_file)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(f"❌ Critical error: Unable to create output directory "
                  f"'{output_dir}'. ({e})")
            sys.exit(1)
        if not os.access(output_dir, os.W_OK | os.X_OK):
            print(f"❌ Critical error: No write/execute permission "
                  f"for directory '{output_dir}'.")
            sys.exit(1)
    else:
        # If output_file is just a file name in the current directory
        if not os.access(".", os.W_OK | os.X_OK):
            print("❌ Critical error: No write permission in the "
                  "current directory.")
            sys.exit(1)

    # If the output file already exists, check if it's writable
    if os.path.exists(output_file):
        if not os.path.isfile(output_file):
            print(f"❌ Critical error: Output path '{output_file}' "
                  f"exists but is not a file.")
            sys.exit(1)

        out_stat = os.stat(output_file)
        if not bool(out_stat.st_mode & stat.S_IWUSR):
            print(f"❌ Critical error: No write permission "
                  f"for output file '{output_file}'.")
            sys.exit(1)

        if not os.access(output_file, os.W_OK):
            print(f"❌ Critical error: No write permission "
                  f"for output file '{output_file}'.")
            sys.exit(1)

    return input_file, output_file, def_file
