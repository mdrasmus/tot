VENV_DIR=env
VENV=. env/bin/activate

setup: $(VENV_DIR)

$(VENV_DIR): requirements-dev.txt
	virtualenv $(VENV_DIR)
	$(VENV) && pip install -r requirements-dev.txt

teardown:
	rm -rf $(VENV_DIR)

test:
	nosetests -sv tot

.PHONY: teardown
