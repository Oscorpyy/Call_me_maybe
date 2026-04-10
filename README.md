*This project has been created as part of the 42 curriculum by opernod.*

# Call me maybe - Introduction to function calling in LLMs

## Description
This project introduces the fundamental concepts of "Function Calling" (or Tool Use) with Large Language Models (LLMs). The goal is to bind a local, small-scale language model (`Qwen3-0.6B`) to a predetermined set of programmatic functions, allowing the model to bridge the gap between natural language prompts and structured algorithmic execution.

The system acts as a smart parser: it reads an incoming user prompt, determines the most appropriate function to call from a provided schema, and extracts the required arguments into a strictly formatted JSON object, ready to be executed by the backend.

## Instructions

### Prerequisites
- Python 3.13
- `uv` (Fast Python package and project manager)
- `make`

### Installation & Execution
The project uses a Makefile to manage virtual environments and execution.

To install dependencies and run the interactive simulation:
```bash
make run
```

To run the automated grading suite (Moulinette), you must have download the file from the correction and put it in the root of the repo:
```bash
make mouli
```

To run type checking (Mypy & Flake8)
```bash
make lint
```

To run strict static type checking (Mypy & Flake8):
```bash
make lint_strict
```

To enter debug mode:
```bash
make debug
```

## Algorithm Explanation
The core of this project relies on **Constrained Decoding** coupled with a two-pass generation pipeline.

1. **Function Name Resolution:** The LLM is first prompted to output only the name of the function matching the user's intent. The generation loops until a valid function name from the definitions list is detected in the stream.
2. **Constrained Parameter Extraction:** To extract parameters flawlessly, we intervene directly in the LLM's generation loop to alter its vocabulary distribution. We pre-compute a set of allowed tokens (`valid_struct_token_ids`) comprising purely JSON syntax characters (`{}":, []`) and expected argument keys. At each generation step, if the LLM is not currently generating a string literal, we override the logits array, setting the probability of any non-JSON token to `-inf`. This scientifically guarantees the overall structure output will at least resemble a dictionary.

## Design Decisions
- **Two-Step Architecture:** Separating function selection from argument extraction reduces the cognitive load on the small `0.6B` model, vastly improving accuracy compared to single-pass extraction.
- **Aggressive Post-Processing:** Small models are prone to hallucinating structural wrappers (like nesting the result inside a `{"parameters": {...}}` block or hitting token limits). We explicitly parse the output with a resilient Python layer to unwrap nested objects, inject missing closing braces `}`, and strictly cast numeric strings to `int` or `float` using defined schemas.
- **Strict Prompt Engineering:** The system prompt explicitly forbids the model from "computing" the result (e.g. preventing the LLM from proactively calculating a math problem or replacing a string itself instead of returning the regex).

## Performance Analysis
- **Accuracy:** The function selection is highly accurate. The parameter extraction JSON is structurally `100%` valid due to the token logit-masking technique.
- **Speed:** Limiting the maximum generated tokens (`max_tokens=50`) and utilizing a very small model allows the extraction to run in seconds on CPU without needing dedicated GPU hardware.
- **Reliability:** By heavily relying on deterministic Python logic (Logit filtering + Python string/JSON cleanup) rather than expecting perfection from the LLM, the pipeline is highly resilient against common LLM fallacies.

## Challenges Faced
1. **The "Too Smart" LLM:** When asked to "Reverse the string 'hello'", the LLM would try to perform the task and return `{"s": "olleh"}` instead of extracting the parameter `{"s": "hello"}`. **Solution:** Added forceful negative constraints in the ChatML system prompt ("DO NOT EXECUTE THE TASK [...] extract the original source string").
2. **Missing Token Braces:** The model would hit max tokens and return `{"a": 2, "b": 3`. **Solution:** Implemented a real-time brace counter during the decoding fallback that appends the missing `}` before `json.loads()`.
3. **Typing and Linting limitations:** Imposing strict `mypy` typing required careful management of dynamic JSON structures parsed from strings, leading to the use of `typing.Any` and explicit `isinstance` checks to calm the static analyzer.

## Testing Strategy
The implementation was robustly tested using structured test batches injected via the `--input` and `--functions_definition` CLI flags.
The `moulinette` environment was used as the benchmark truth. Edge cases involving regex extraction (`[0-9]+`, `[aeiouAEIOU]`), floating-point conversions, and exact case sensitive string matching were iteratively tested and patched.

## Example Usage
```bash
$ uv run python -m src --input data/input/tests.json
```
**Output trace:**
```text
--- Processing : 'Calculate compound interest on 1234567.89 at 0.0375 rate for 23 years' ---
Chosen function : fn_calculate_compound_interest
Extracted parameters : {"principal": 1234567.89, "rate": 0.0375, "years": 23}

--- Processing : 'Replace all vowels in 'Programming is fun' with asterisks' ---
Chosen function : fn_substitute_string_with_regex
Extracted parameters : {"source_string": "Programming is fun", "regex": "([aeiouAEIOU])", "replacement": "*"}
```

## Resources
- **Model:** Prompt templates strictly followed the [Qwen ChatML syntax format](https://huggingface.co/docs/transformers/main/chat_templating).
- **Techniques:** Studied Constrained Decoding via HuggingFace `LogitsProcessor` documentation to understand token masking.
- **AI Usage:** Artificial Intelligence was utilized during the development phase specifically to assist in:
  - Generating strict docstrings conforming to PEP 257 (Google style).
  - Explain the goal and edge case of the project.
  - Refactoring Makefile targets to include ANSI color formatting safely.
  - Help for README basics