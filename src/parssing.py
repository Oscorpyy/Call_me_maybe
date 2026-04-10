import sys
import os


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

    # Check if prompts file exists
    if not os.path.isfile(input_file):
        print(f"❌ Critical error: Input file "
              f"'{input_file}' not found.")
        sys.exit(1)

    # Check if definitions file exists
    if not os.path.isfile(def_file):
        print(f"❌ Critical error: Definitions file "
              f"'{def_file}' not found.")
        sys.exit(1)

    # Ensure output file parent directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(f"❌ Critical error: Unable to create output directory "
                  f"'{output_dir}'. ({e})")
            sys.exit(1)

    return input_file, output_file, def_file
