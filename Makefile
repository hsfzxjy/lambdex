# PY=${py}
ifeq (${PY}, )
	PY=python3
endif
test:
	${PY} -m unittest discover tests
test_fmt:
	${PY} -m unittest discover fmt_tests
