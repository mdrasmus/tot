VENV_DIR=env
VENV=. env/bin/activate

setup: $(VENV_DIR)

$(VENV_DIR): requirements-dev.txt
	virtualenv $(VENV_DIR)
	$(VENV) && pip install -r requirements-dev.txt

teardown:
	rm -rf $(VENV_DIR)

test-data:
	bin/tot \
	    --log tot/test_data/chdir.log \
	    --log-fs tot/test_data/chdir.fs.log \
	    log bash -c 'cd tmp; echo hello | cat > out'

test:
	$(VENV) && nosetests -sv tot

.PHONY: setup teardown test test-data
