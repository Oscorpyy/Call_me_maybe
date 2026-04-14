import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"


import json  # noqa: E402
from llm_sdk import Small_LLM_Model  # noqa: E402


def get_fc_name(prompt: str, fc_def: list[dict[str, str]]) -> str:
    """Retrieves the called function name using the LLM.

    Args:
        prompt (str): The user's prompt.
        fc_def (list[dict[str, str]]): Valid function definitions.

    Returns:
        str: The function name extracted by the model.
    """
    llm = Small_LLM_Model()

    fc_def_str = json.dumps(fc_def)

    prompt_1 = (
        "<|im_start|>system\n"
        "Choose a function.\n"
        f"Available functions:\n{fc_def_str}<|im_end|>\n"
        "<|im_start|>user\n"
        f"{prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
        "Function name: "
    )

    # Encode only the full construct
    tokens = llm.encode(prompt_1).tolist()[0]
    len_tokens = len(tokens)
    name_found = False

    fc_name = ""

    valid_names = [func["name"] for func in fc_def if "name" in func]
    eos_token = llm.encode("<|im_end|>").tolist()[0][0]

    while not name_found:
        logits = llm.get_logits_from_input_ids(tokens)
        next_token_id = logits.index(max(logits))

        if next_token_id == eos_token:
            break

        tokens.append(next_token_id)

        generated_text = llm.decode(tokens[len_tokens:]).strip()

        for name in valid_names:
            if name in generated_text:
                fc_name = name
                name_found = True
                break

    if not name_found:
        fc_name = llm.decode(tokens[len_tokens:]).strip()

    return fc_name
