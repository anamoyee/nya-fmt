def _convert[T: object, TypeInstance: object](value: tuple[T] | T, Type: type[TypeInstance]) -> TypeInstance | T:
	"""Should be called `_tuple_to_Type_recursively()`, but that name is too cumbersome to use.

	Returns:
		The given tuple literal

	"""
	if isinstance(value, tuple):
		return Type(_convert(v, Type) for v in value)
	return value


def test_nonhash_iterable(π):
	for Type, Type__display_name in π.parametrize(
		(tuple, tuple.__name__),
		(list, list.__name__),
		(lambda xs: (x for x in xs), "generator"),  # generator
	):
		π[Type__display_name] = _convert((), Type)
		π[Type__display_name] = _convert((1,), Type)
		π[Type__display_name] = _convert((((1, 2, 3),),), Type)
		π[Type__display_name] = _convert((1, (2, (3,))), Type)
		π[Type__display_name] = _convert(((((((((),),),),),),),), Type)


def test_set(π):
	for Set in π.parametrize(
		set,
		frozenset,
	):
		Set: type
		Set__display_name: str = Set.__name__

		π[Set__display_name] = Set(set())
		π[Set__display_name] = Set({1})
		π[Set__display_name] = Set({1, 2, 3})
