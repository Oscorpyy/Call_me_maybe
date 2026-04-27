VENV = .venv
unexport VIRTUAL_ENV
PY = $(VENV)/bin/python3

SRC_DIR = src

$(VENV)/bin/activate: pyproject.toml
	@printf "\033[34mCreating virtual environment...\033[0m\n"
	@uv venv $(VENV)
	@printf "\033[34mInstalling dependencies...\033[0m\n"
	@if [ -f requirements.txt ]; then $(UV) install --quiet -r requirements.txt; fi
	uv sync
	@touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

run: install
	@printf "\033[32mRunning the simulation with ia...\033[0m\n"
	@uv run python -m src

debug: install
	@printf "\033[33m--------------------------------------------------------\033[0m\n"
	@printf "\033[33mMode Debug (pdb) activé\033[0m\n"
	@printf "  -> \033[33ms\033[0m (step)  : Avance ligne par ligne (entre dans les fonctions)\n"
	@printf "  -> \033[33mn\033[0m (next)  : Avance ligne par ligne (sans entrer)\n"
	@printf "  -> \033[33mc\033[0m (cont)  : Continue jusqu'au prochain point d'arrêt\n"
	@printf "  -> \033[33ml\033[0m (list)  : Affiche le code autour de la ligne actuelle\n"
	@printf "  -> \033[33mq\033[0m (quit)  : Quitte le debugger\n"
	@printf "\033[33m--------------------------------------------------------\033[0m\n"
	@uv run python -m pdb -m src

clean:
	@printf "\033[34mCleaning up...\033[0m\n"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.log" -delete
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@printf "\033[31mRemoving virtual environment...\033[0m\n"
	@rm -rf $(VENV)
	@printf "\033[31mRemoving output files...\033[0m\n"
	@rm -rf data/output
	@printf "\033[34mCleanup complete.\033[0m\n"

re: clean run

lint: install
	@printf "\033[34mRunning flake8...\033[0m\n"
	@uv run python -m flake8 --max-line-length=120 $(SRC_DIR)/ && printf "\033[32m[OK]\033[0m Flake8\n"
	@printf "\033[34mRunning mypy...\033[0m\n"
	@uv run python -m mypy $(SRC_DIR)/ --warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs && printf "\033[32m[OK]\033[0m Mypy\n"
	@printf "\033[34mLinting complete.\033[0m\n"

lint-strict: install
	@printf "\033[34mRunning flake8 with strict settings...\033[0m\n"
	@uv run python -m flake8 --max-line-length=120 $(SRC_DIR)/ && printf "\033[32m[OK]\033[0m Flake8\n"
	@printf "\033[34mRunning mypy with strict settings...\033[0m\n"
	@uv run python -m mypy $(SRC_DIR)/ --strict && printf "\033[32m[OK]\033[0m Mypy\n"
	@printf "\033[34mStrict linting complete.\033[0m\n"

mouli : install
	@printf "\033[34mRunning moulinette for grading...\033[0m\n"
	@uv sync
	@printf "\033[34mPreparing exercises...\033[0m\n"
	@cd moulinette && uv run python -m moulinette prepare_exercises --set private
	@printf "\033[34mRunning the simulation with ia for grading...\033[0m\n"
	@uv run python -m src --input moulinette/data/input/function_calling_tests.json --functions_definition moulinette/data/input/functions_definition.json
	@printf "\033[34mGrading student answers...\033[0m\n"
	@cd moulinette && uv run python -m moulinette grade_student_answers --set private --student_answer_path ../data/output/function_calling_results.json


.PHONY: install run debug clean re lint lint-strict mouli
