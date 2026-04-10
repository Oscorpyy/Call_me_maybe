# uv run python -m src [--functions_definition <function_definition_file>]
# [--input <input_file>] [--output <output_file>]

import os
import json
from typing import Any
from src.get_fc_name import get_fc_name
from src.get_fc_result import get_fc_result
from src.parssing import parse_and_validate_args
from llm_sdk import Small_LLM_Model


def main() -> None:
    """Main entry point of the program.

    Parses arguments, loads input files, calls the extraction process
    on each prompt, and saves the list of extracted parameters
    into the output file.
    """
    # 1. LLM initialization
    llm = Small_LLM_Model()
    name = llm._model_name
    fc_tests_path, fc_output_path, fc_def_path = parse_and_validate_args()
    print(f"fc_tests_path: {fc_tests_path}")
    print(f"fc_output_path: {fc_output_path}")
    print(f"fc_def_path: {fc_def_path}")
    print(f"LLM Model Name: {name}")

    try:
        with open(fc_tests_path, "r") as f:
            tests_data = json.load(f)  # Load the list of prompt dicts
        with open(fc_def_path, "r") as f:
            input_data = f.read()
    except FileNotFoundError as e:
        print(f"Error : File not found : {e}")
        return

    results_list = []
    # Iterate over all tests (prompts)
    for test in tests_data:
        prompt_text = test.get("prompt", "")
        if not prompt_text:
            continue

        print(f"\n--- Processing : '{prompt_text}' ---")
        prompt_result, errors = get_fonction_result(input_data, prompt_text)
        results_list.append(prompt_result)

    # Save all results in the output file
    os.makedirs(os.path.dirname(fc_output_path), exist_ok=True)
    with open(fc_output_path, "w") as f:
        json.dump(results_list, f, indent=4)

    print(f"\nResults saved in {fc_output_path} for "
          f"\033[32m{len(results_list)} tests \033[0m with \033[31m{errors} "
          "JSON decoding errors \033[0m.")


def get_fonction_result(function_definitions_raw: str,
                        prompt: str) -> tuple[dict[str, Any], int]:
    """Determines the function to call and extracts its parameters.

    Args:
        function_definitions_raw (str): Raw system definitions in JSON.
        prompt (str): Request entered by the user.

    Returns:
        tuple[dict[str, Any], int]: The results (prompt, name, parameters)
        along with the number of JSON parsing errors encountered.
    """
    error = 0
    try:
        defs = json.loads(function_definitions_raw)
        filtered_defs = [{"name": func.get("name"),
                          "description": func.get(
                              "description")} for func in defs]
    except json.JSONDecodeError:
        filtered_defs = []
        defs = []

    fc_name = get_fc_name(prompt, filtered_defs)

    result_dict = {
        "prompt": prompt,
        "name": fc_name,
        "parameters": {}
    }

    if fc_name and "Erreur" not in fc_name and defs:
        fc_result = get_fc_result(prompt, fc_name, defs)

        # Robust JSON extraction
        clean_result = fc_result
        start_idx = clean_result.find('{')

        # To avoid issues with multiple outputs,
        # we look for the first complete JSON
        if start_idx != -1:
            try:
                start_idx = clean_result.find('{')
                end_idx = clean_result.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                    clean_result = clean_result[start_idx:end_idx+1]
            except Exception:
                end_idx = clean_result.rfind('}')
                if end_idx >= start_idx:
                    clean_result = clean_result[start_idx:end_idx+1]

        try:
            result_json = json.loads(clean_result)

            result_dict["parameters"] = result_json

            print(f"Chosen function : {fc_name}")
            print(f"Extracted parameters : {json.dumps(result_json)}")

        except json.JSONDecodeError:
            error += 1
            print(f"Chosen function : {fc_name}")
            print(f"\033[33mError decoding the parameters JSON: "
                  f"{clean_result}\033[0m")

    return result_dict, error


if __name__ == "__main__":
    main()
