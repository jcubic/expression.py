VERSION = 0.1.0

.PHONY: all install publish publish-test version build clean test coverage lint parser

all: version build

install: build
	pip install -e .

publish: version build
	twine upload dist/*

publish-test: version build
	twine upload --repository testpypi dist/*

build: clean parser
	python -m build

parser: expression/parser.py

expression/parser.py: expression/grammar.peg
	python -m pegen expression/grammar.peg -o expression/parser.py

clean:
	rm -rf dist/ build/ *.egg-info/
	rm -f expression/parser.py

test: parser
	python -m pytest tests/ -v

coverage: parser
	python -m pytest tests/ -v --cov=expression --cov-report=term --cov-report=lcov:coverage.lcov

lint:
	ruff check expression/ tests/

version:
	sed -i 's/^version = "[0-9]\+\.[0-9]\+\.[0-9]\+"/version = "$(VERSION)"/' pyproject.toml
	sed -i 's/^VERSION = [0-9]\+\.[0-9]\+\.[0-9]\+/VERSION = $(VERSION)/' Makefile
	sed -i 's|pip-[0-9]\+\.[0-9]\+\.[0-9]\+-blue|pip-$(VERSION)-blue|' README.md
