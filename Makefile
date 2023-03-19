.EXPORT_ALL_VARIABLES:

PWD = $(shell pwd)
D8Y_AUTH_CONFIG_FILE ?= ${PWD}/tests/data/auth_config
D8Y_AUTH_CACHE_FILE ?= ${PWD}/tests/data/auth

install_pip_tools:
	pip install pip-tools

pip_compile: install_pip_tools
	pip-compile --quiet --no-emit-index-url requirements.in
	pip-compile --quiet --no-emit-index-url requirements-test.in

pip_sync: install_pip_tools
	pip-sync requirements.txt requirements-test.txt

install_develop: pip_compile pip_sync
	python setup.py develop

lint: install_develop
	pre-commit run --all-files

auth: install_develop
	python tests/tools/authenticate.py

test: install_develop
	pytest -s tests

ci: auth test
