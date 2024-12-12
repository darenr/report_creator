all: setup examples
.PHONY: clean examples

EXAMPLES = $(wildcard examples/*.py)

setup:
	@echo "Setting up environment..."
	@python3 -m pip install -q --upgrade pip
	@python3 -m pip install -qr requirements.txt -U
	@python3 -m pip install -qr requirements-doc.txt -U
	@python3 -m pip install -qr requirements-test.txt -U
	@echo "Installing/updating dev tools..."
	@python3 -m pip install -q ruff twine -U

examples: setup
	@for file in $(EXAMPLES); do \
		echo "building example: $$file"; \
        PYTHONPATH=. python $$file; \
	done	

docs: setup clean
	@cd docs && make html
	@open docs/build/html/index.html

clean:
	@rm -rf build dist *.egg-info __pycache__
	cd docs && make clean

format:
	@ruff format report_creator
	@ruff check report_creator
	@python scripts/utils/ruffen-docs.py README.md

release: setup clean
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;

	@python3 setup.py sdist bdist_wheel
	@twine upload dist/*

tests: setup
	@python3  -c 'import report_creator; print(report_creator.__version__)'
	@python3 -m pytest -vs tests	

.PHONY: targets
targets:
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'
