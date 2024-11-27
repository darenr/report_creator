all: setup examples
.PHONY: clean examples

EXAMPLES = $(wildcard examples/*.py)

setup:
	@python3 -m pip install -q --upgrade pip
	@python3 -m pip install -qr requirements.txt -U
	@python3 -m pip install -qr requirements-docs.txt -U
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
	@rm -rf build dist *.egg-info
	cd docs && make clean

debug:
	@echo "EXAMPLES: $(EXAMPLES)"

format:
	@ruff format report_creator
	@ruff check report_creator

deploy: setup clean
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;

	@python3 setup.py sdist bdist_wheel
	@twine upload dist/*

