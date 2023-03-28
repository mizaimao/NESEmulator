# system python interpreter. used only to create virtual environment
PY = python3
VENV = .venv
BIN=$(VENV)/bin
TEMP=temp


.PHONY: venv
venv: clean standard_venv post_venv

.PHONY: standard_venv
standard_venv:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade -r requirements.txt
	touch $(VENV)


.PHONY: post_venv
post_venv:
	$(BIN)/pip install -e .
	
.PHONY: test
test: $(VENV)
	$(BIN)/pytest

.PHONY: lint
lint: $(VENV)
	pylint

.PHONY: clean
clean:
	deactivate
	rm -rf $(VENV)
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete