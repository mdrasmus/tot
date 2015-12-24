VENV_DIR=env
VENV=. env/bin/activate

setup: $(VENV_DIR)

$(VENV_DIR): requirements.txt
	virtualenv $(VENV_DIR)
	$(VENV) && pip install -r requirements.txt

teardown:
	rm -rf $(VENV_DIR)

.PHONY: teardown
