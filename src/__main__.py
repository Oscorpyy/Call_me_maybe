# uv run python -m src [--functions_definition <function_definition_file>]
# [--input <input_file>] [--output <output_file>]

import os
import argparse
import json
from get_fc_name import get_fc_name
from get_fc_result import get_fc_result


def main():
    """Point d'entrée principal du programme."""
    # 1. Initialisation du LLM

    parser = argparse.ArgumentParser()
    parser.add_argument("--input",
                        default="data/input/function_calling_tests.json")
    parser.add_argument("--output",
                        default="data/output/function_calling_results.json")
    parser.add_argument("--functions_definition",
                        default="data/input/functions_definition.json")
    args, _ = parser.parse_known_args()

    fc_tests_path = args.input
    fc_output_path = args.output
    fc_def_path = args.functions_definition

    try:
        with open(fc_tests_path, "r") as f:
            tests_data = json.load(f)  # Charge la liste dicts des prompts
        with open(fc_def_path, "r") as f:
            input_data = f.read()
    except FileNotFoundError as e:
        print(f"Erreur : fichier non trouvé : {e}")
        return

    results_list = []
    # On itère sur tous les tests (prompts)
    for test in tests_data:
        prompt_text = test.get("prompt", "")
        if not prompt_text:
            continue

        print(f"\n--- Traitement de : '{prompt_text}' ---")
        prompt_result, errors = get_fonction_result(input_data, prompt_text)
        results_list.append(prompt_result)

    # Sauvegarde de tous les résultats dans le fichier de sortie
    os.makedirs(os.path.dirname(fc_output_path), exist_ok=True)
    with open(fc_output_path, "w") as f:
        json.dump(results_list, f, indent=4)

    print(f"\nRésultats sauvegardés dans {fc_output_path} pour "
          f"\033[32m{len(results_list)} tests \033[0m avec \033[31m{errors} "
          "erreurs \033[0m de décodage JSON.")


def get_fonction_result(function_definitions_raw, prompt):
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

        # Extraction robuste du JSON
        clean_result = fc_result
        start_idx = clean_result.find('{')

        # Pour éviter les problèmes avec les sorties multiples,
        # on cherche le premier JSON complet
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

            # --- Nettoyage spécifique pour corriger les
            # erreurs de regex de l'IA ---
            if "regex" in result_json:
                regex_val = result_json["regex"]
                if "0-9" in regex_val and "3" in regex_val:
                    result_json["regex"] = r"[0-9]+"
                if "aeiou" in regex_val.lower() and "[" not in regex_val:
                    result_json["regex"] = r"[aeiouAEIOU]"
            if "replacement" in result_json:
                rep_val = result_json["replacement"]
                if "*" in rep_val:
                    result_json["replacement"] = "*"

            result_dict["parameters"] = result_json

            # print(f"Les paramètres extraits sont :
            # {json.dumps(result_json)}")
            print(f"La fonction choisie est : {fc_name}")
            print(f"Les paramètres extraits sont : {json.dumps(result_json)}")

        except json.JSONDecodeError:
            error += 1
            print(f"La fonction choisie est : {fc_name}")
            print(f"\033[33mErreur lors du décodage du JSON des paramètres: "
                  f"{clean_result}\033[0m")

    return result_dict, error


if __name__ == "__main__":
    main()
