from llm_sdk import Small_LLM_Model


def get_fc_name(prompt: str, fc_def: list) -> str:
    """Fonction de test pour récupérer le nom de la fonction appelée."""
    llm = Small_LLM_Model()

    import json
    fc_def_str = json.dumps(fc_def)

    system_prompt = (
        "Choose a fonction"
        f"Available functions:\n{fc_def_str}\n\n"
        f"User prompt: {prompt}\n"
        "Function name: "
    )

    # Encoder seulement le construct complet
    tokens = llm.encode(system_prompt).tolist()[0]
    len_tokens = len(tokens)
    name_found = False

    fc_name = ""

    valid_names = [func["name"] for func in fc_def if "name" in func]

    eos_token = llm._tokenizer.eos_token_id

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
