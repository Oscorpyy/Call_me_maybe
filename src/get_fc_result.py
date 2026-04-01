import json
from llm_sdk import Small_LLM_Model


def get_float_results(json_str: str) -> str:
    """Verifie si les valeurs sont des int"""
    try:
        data = json.loads(json_str)
        print(f"{data}")
        for key, value in data.get("parameters", {}).items():
            if value.get("type") == "number":
                data[key] = float(value)
        return json.dumps(data)
    except json.JSONDecodeError:
        return json_str


def get_num_results(json_str: str) -> str:
    """Verifie si les valeurs sont des int"""
    try:
        data = json.loads(json_str)
        print(f"{data}")
        for key, value in data.get("parameters", {}).items():
            if value.get("type") == "integer":
                data[key] = int(value)
                print(f"\n\n\n\n\n int(value): {int(value)}")
        return json.dumps(data)
    except json.JSONDecodeError:
        return json_str


def get_fc_result(prompt: str, function_name: str, fc_def_full: list) -> str:
    """Fonction pour extraire les arguments nécessaires à la fonction."""
    llm = Small_LLM_Model()

    target_func = None
    for func in fc_def_full:
        if func.get("name") == function_name:
            target_func = func
            break

    if not target_func:
        return "Erreur: Fonction non trouvée"

    # Convertir en chaîne de caractères
    func_def_str = json.dumps(target_func, indent=2)

    system_prompt = (
        "Output ONLY a single valid JSON object representing "
        "the parameters values. Do not output anything else.\n"
        f"Function definition:\n{func_def_str}\n\n"
        f"User prompt: {prompt}\n"
        "Parameters JSON:\n{"
    )

    tokens = llm.encode(system_prompt).tolist()[0]
    len_tokens = len(tokens)
    eos_token = llm._tokenizer.eos_token_id

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
                    # N'ajoute pas -inf à eos si on a une forme finie
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

    for k, v in target_func.get("parameters", {}).items():
        if v.get("type") == "number":
            result_str = get_float_results(result_str)
    for k, v in target_func.get("parameters", {}).items():
        if v.get("type") == "integer":
            result_str = get_num_results(result_str)

    return result_str
