.PHONY: install lint test format build clean

install:
	python -m pip install -r requirements-dev.txt

lint:
	ruff check .
	black --check .
	mypy BESTLIB

test:
	pytest --maxfail=1

format:
	black .
	ruff check . --fix

build:
	@if [ -d js ]; then (cd js && npm install && npm run build); fi
	python -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache

