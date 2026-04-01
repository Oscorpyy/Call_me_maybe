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
    parser.add_argument("--fc_tests",
                        default="/home/opernod/42/cm/moulinette/data/input/function_calling_tests.json")
    parser.add_argument("--fc_output",
                        default="/home/opernod/42/cm/moulinette/data/correction/function_calling_corrections.json")
    parser.add_argument("--fc_def",
                        default="/home/opernod/42/cm/moulinette/data/input/functions_definition.json")
    args, _ = parser.parse_known_args()

    fc_tests_path = args.fc_tests
    fc_output_path = args.fc_output
    fc_def_path = args.fc_def

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
        prompt_result = get_fonction_result(input_data, prompt_text)
        results_list.append(prompt_result)

    # Sauvegarde de tous les résultats dans le fichier de sortie
    os.makedirs(os.path.dirname(fc_output_path), exist_ok=True)
    with open(fc_output_path, "w") as f:
        json.dump(results_list, f, indent=4)

    print(f"\nRésultats sauvegardés dans {fc_output_path}")


def get_fonction_result(function_definitions_raw, prompt):
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
                # On cherche le dernier bloc complet
                # au lieu de s'arrêter bêtement au premier "}" inclus dans le texte
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
            print(f"La fonction choisie est : {fc_name}")
            print(f"Erreur lors du décodage du JSON des paramètres :"
                  f"{clean_result}")

    return result_dict


if __name__ == "__main__":
    main()
