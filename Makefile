# PY=${py}
ifeq (${PY}, )
	PY=python3
endif
test:
	${PY} -m unittest discover tests/compiler/
test_fmt:
	${PY} -m unittest discover tests/fmt/
test_repl_builtin:
	${PY} -m unittest tests/repl/*builtin*
test_repl_idle:
	${PY} -m unittest tests/repl/*idle*
