VENV = .venv
PIP = $(VENV)/bin/pip
PYTHON = $(VENV)/bin/python3


venv: setup.py
	test -d $(VENV) || python3 -m venv $(VENV)


install: venv
	. $(VENV)/bin/activate
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .


install_dev: venv
	. $(VENV)/bin/activate
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]


run_test: install_dev
	. $(VENV)/bin/activate
	$(PYTHON) -m pytest


clean:
	rm -rf .pytest_cache
	rm -rf flaky_tests_detection/__pycache__
	rm -rf flaky_tests_detection.egg-info
	rm -rf tests/__pycache__
	rm -rf $(VENV)


publish: install_dev
	. $(VENV)/bin/activate && $(VENV)/bin/semantic-release publish -D version_variable=flaky_tests_detection/__init__.py:__version__