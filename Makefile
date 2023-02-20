.EXPORT_ALL_VARIABLES:

install_pip_tools:
	pip install pip-tools

pip_compile: install_pip_tools
	pip-compile --quiet --no-emit-index-url requirements.in
	pip-compile --quiet --no-emit-index-url requirements-test.in

pip_sync: install_pip_tools
	pip-sync requirements.txt requirements-test.txt

install_develop: pip_compile pip_sync
	python setup.py develop

test:
	pytest tests
