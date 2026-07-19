import nya_fmt as nf


def add_outer(x: int, y: int) -> int:
	return x + y


def test_function(π):
	for _ in π.parametrize_providers(
		nf.providers.pystdlib.FP__types__FunctionType_VIA_module_path,
		nf.providers.pystdlib.FP__types__FunctionType_VIA_def,
	):

		@π
		def add_inner(x: int, y: int) -> int:
			return x + y

		π << add_outer


lambda_add_outer = lambda x, y: x + y  # ruff:ignore[lambda-assignment]


def test_lambda(π):
	lambda_add_inner = lambda x, y: x + y  # ruff:ignore[lambda-assignment]

	π << lambda_add_inner
	π << lambda_add_outer
