VENV = .venv
PY = $(VENV)/bin/python3

SRC_DIR = src
NAME = $(SRC_DIR)/__main__.py

$(VENV)/bin/activate: pyproject.toml
	@echo "Creating virtual environment..."
	@uv venv $(VENV)
	@echo "Installing dependencies..."
	@if [ -f requirements.txt ]; then $(UV) install --quiet -r requirements.txt; fi
	uv sync
	@touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

run: install
	@$(PY) $(NAME)

debug: install
	@echo "--------------------------------------------------------"
	@echo "Mode Debug (pdb) activé pour $(NAME)"
	@echo "  -> 's' (step)  : Avance ligne par ligne (entre dans les fonctions)"
	@echo "  -> 'n' (next)  : Avance ligne par ligne (sans entrer)"
	@echo "  -> 'c' (cont)  : Continue jusqu'au prochain point d'arrêt"
	@echo "  -> 'l' (list)  : Affiche le code autour de la ligne actuelle"
	@echo "  -> 'q' (quit)  : Quitte le debugger"
	@echo "--------------------------------------------------------"
	@$(PY) -m pdb $(NAME)

clean:
	@echo "Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.log" -delete
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@echo "Cleanup complete."

re: clean run

lint: install
	@echo "Running flake8..."
	@$(PY) -m flake8 --max-line-length=120 $(SRC_DIR)/ && printf "\033[32m[OK]\033[0m Flake8\n"
	@echo "Running mypy..."
	@$(PY) -m mypy $(SRC_DIR)/ --warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs && printf "\033[32m[OK]\033[0m Mypy\n"
	@echo "Linting complete."

lint_strict: install
	@echo "Running flake8 with strict settings..."
	@$(PY) -m flake8 --max-line-length=120 $(SRC_DIR)/ && printf "\033[32m[OK]\033[0m Flake8\n"
	@echo "Running mypy with strict settings..."
	@$(PY) -m mypy $(SRC_DIR)/ --strict && printf "\033[32m[OK]\033[0m Mypy\n"
	@echo "Strict linting complete."

.PHONY: install run debug clean re lint lint_strict
