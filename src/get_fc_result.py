# import os
import json
from typing import Any
from llm_sdk import Small_LLM_Model


def get_float_results(json_str: str, key: str) -> str:
    """Checks if values are floats and converts them.

    Args:
        json_str (str): The JSON string containing the parameters.
        key (str): The parameter key to convert to float.

    Returns:
        str: The updated JSON string, or original string on error.
    """
    try:
        data = json.loads(json_str)
        target_dict = data["parameters"] if "parameters" in data else data
        if key in target_dict:
            target_dict[key] = float(target_dict[key])
        return json.dumps(data)
    except (json.JSONDecodeError, ValueError, TypeError):
        return json_str


def get_num_results(json_str: str, key: str) -> str:
    """Checks if values are ints and converts them.

    Args:
        json_str (str): The JSON string containing the parameters.
        key (str): The parameter key to convert to int.

    Returns:
        str: The updated JSON string, or original string on error.
    """
    try:
        data = json.loads(json_str)
        target_dict = data["parameters"] if "parameters" in data else data

        if key in target_dict:
            target_dict[key] = int(target_dict[key])
        return json.dumps(data)
    except (json.JSONDecodeError, ValueError, TypeError):
        return json_str


def get_fc_result(prompt: str, function_name: str,
                  fc_def_full: list[dict[str, Any]]) -> str:
    """Extracts the necessary arguments for the function from the prompt.

    Args:
        prompt (str): The user's prompt.
        function_name (str): The target function's name.
        fc_def_full (list[dict[str, Any]]): Full function definitions schema.

    Returns:
        str: A JSON string of the extracted parameters.
    """
    llm = Small_LLM_Model()

    target_func = None
    for func in fc_def_full:
        func_name = func.get("name")
        if isinstance(func_name, str) and func_name == function_name:
            target_func = func
            break

    if not target_func:
        return "Error: Function not found"

    # Convert to string
    func_def_str = json.dumps(target_func, indent=2)

    prompt_2 = (
            "<|im_start|>system\n"
            "You are an expert data extractor. Your ONLY job is to extract the"
            "arguments from the user's prompt to match the given"
            "function schema.\n\n"
            f"Function:\n{func_def_str}\n\n"
            "CRITICAL RULES:\n"
            "1. Return ONLY a valid JSON object.\n"
            "2. DO NOT EXECUTE THE TASK. or example, if asked to reverse"
            "or modify a string, extract the original source string, NOT the"
            "result.\n 3. If a parameter is a regular expression, ensure the"
            "pattern matches both UPPERCASE and LOWERCASE letters"
            "appropriately based on the prompt's intent.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"{prompt}<|im_end|>\n"
            "<|im_start|>assistant\n"
            "{"
        )
    tokens = llm.encode(prompt_2).tolist()[0]
    len_tokens = len(tokens)
    eos_token = llm.encode("<|im_end|>").tolist()[0][0]

    max_tokens = 50

    expected_keys = list(target_func.get("parameters", {}).keys())

    vocab_path = llm.get_path_to_vocab_file()
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    allowed_struct_chars = set('{}":, []0123456789.-\n\r\t')
    for k in expected_keys:
        allowed_struct_chars.update(k)

    allowed_struct_chars.update("ĠĊ \u0120")

    valid_struct_token_ids = {
        idx for text, idx in vocab.items()
        if all(c in allowed_struct_chars for c in text)
    }

    neg_inf = -float('inf')

    for _ in range(max_tokens):
        logits = llm.get_logits_from_input_ids(tokens)
        current_text = llm.decode(tokens[len_tokens:])

        in_string = current_text.replace('\\"', '').count('"') % 2 != 0

        if not in_string:
            for i in range(len(logits)):
                if i not in valid_struct_token_ids:
                    logits[i] = neg_inf

        if not in_string:
            if current_text.strip().endswith('}'):
                if eos_token < len(logits):
                    pass
            else:
                if eos_token < len(logits):
                    logits[eos_token] = neg_inf

        next_token_id = logits.index(max(logits))

        if next_token_id == eos_token:
            break

        tokens.append(next_token_id)

        current_text_post = llm.decode(tokens[len_tokens:])
        in_string_post = current_text_post.replace(
            '\\"', '').count('"') % 2 != 0

        if not in_string_post and current_text_post.strip().endswith('}'):
            break

    generated_text = llm.decode(tokens[len_tokens:]).strip()
    result_str = "{" + generated_text

    open_braces = result_str.count("{")
    close_braces = result_str.count("}")
    if open_braces > close_braces:
        result_str += "}" * (open_braces - close_braces)

    for k, v in target_func.get("parameters", {}).items():
        if v.get("type") == "number":
            result_str = get_float_results(result_str, k)
    for k, v in target_func.get("parameters", {}).items():
        if v.get("type") == "integer":
            result_str = get_num_results(result_str, k)

    try:
        final_data = json.loads(result_str)
        if "parameters" in final_data and isinstance(
                final_data["parameters"], dict):
            return json.dumps(final_data["parameters"])
        if "name" in final_data and "name" not in expected_keys:
            del final_data["name"]
            return json.dumps(final_data)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return result_str
