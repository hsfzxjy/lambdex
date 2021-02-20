ifeq (${PY}, )
	PY=python3
endif

ifeq (${OPT}, )
	OPT=
endif

clear_cache:
	find tests -name '*.py[co]' -exec rm -rf '{}' \;

test: clear_cache
	${PY} -m unittest discover tests/compiler/ ${OPT}
test_fmt: clear_cache
	${PY} -m unittest discover tests/fmt/ ${OPT}
test_repl_builtin: clear_cache
	${PY} -m unittest tests/repl/*builtin* ${OPT}
test_repl_ipython: clear_cache
	${PY} -m unittest tests/repl/*ipython* ${OPT}
test_repl_idle: clear_cache
	${PY} -m unittest tests/repl/*idle* ${OPT}
test_asm: clear_cache
	${PY} -m unittest discover tests/asm/ ${OPT}