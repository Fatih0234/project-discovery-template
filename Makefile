.PHONY: install test analyze example clean

LIB ?= tenacity

install:
	pip install -e .[dev]

test:
	pytest tests/ -v

analyze:
	libexplorer analyze $(LIB) --language python --top-k 5

example:
	libexplorer analyze tenacity --language python --top-k 5
	@echo ""
	@echo "==> Report saved to reports/tenacity/final_report.md"

clean:
	rm -rf data/ reports/ __pycache__ src/libexplorer/__pycache__ .pytest_cache
