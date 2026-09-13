from .conftest import π_t


def _convert(value, Type):
	"""Should be called `_tuple_to_Type_recursively()`, but that name is too cumbersome to use.

	Returns:
		The given tuple literal

	"""
	if isinstance(value, tuple):
		return Type(_convert(v, Type) for v in value)
	return value


def test_nonhash_iterable(π: π_t):
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


def test_set(π: π_t):
	for Set in π.parametrize(
		set,
		frozenset,
	):
		Set: type

		π[Set.__name__] = Set(set())
		π[Set.__name__] = Set({1})
		π[Set.__name__] = Set({1, 2, 3})


def test_dict(π: π_t):
	π << {}
	π << {"a": 1}
	π << {"a": 1, "b": 2, "c": 3}


def test_infinite_generator(π: π_t):
	with π.fmt.with_tmp_settings():
		π.fmt.iterable_max_display_len = 3

		def infinite_generator():
			while True:
				yield 1

		π << infinite_generator()


def test_iterable_max_display_len_overflow_on_listlike(π: π_t):
	with π.fmt.with_tmp_settings():
		π.fmt.iterable_max_display_len = 3

		for Type, Type__display_name in π.parametrize(
			(tuple, tuple.__name__),
			(list, list.__name__),
			(set, set.__name__),
			(frozenset, frozenset.__name__),
		):
			π[Type__display_name] = Type(range(10))


def test_iterable_max_display_len_overflow_on_mappinglike(π: π_t):
	with π.fmt.with_tmp_settings():
		π.fmt.iterable_max_display_len = 3

		π << {i: i for i in range(10)}


def test_recursive_reference_list(π: π_t):
	lst = [1, 2, 3]
	lst.append(lst)
	π << lst

	π.hr()

	a = a[0] = [None]

	π << a
