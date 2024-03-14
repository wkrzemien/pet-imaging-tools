PYTHON_SRCS=$(shell find . -name "*py" -not -path "./venv-*")
PYTHON_WITHOUT_TESTS_SRCS=$(shell find . -name "*py" -not -path "./tests/*" -not -path "./venv-*")
ifeq (, $(shell which yapf))
$(error "No yapf in $(PATH), consider doing pip install yapf")
endif

format: ${PYTHON_SRCS}
	yapf -i $?

lint: ${PYTHON_WITHOUT_TESTS_SRCS}
	pylint $?

check-compile-python: ${PYTHON_SRCS}
	for src in ${PYTHON_SRCS}; do \
		python -m py_compile $${src}; \
	done

.PHONY: tests
tests:
	python -m pytest
