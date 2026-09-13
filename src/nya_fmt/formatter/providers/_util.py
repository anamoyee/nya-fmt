def isinstance_getitem[T](dct: dict[type, T], key: object) -> T:
	"""Non efficient getitem but the keylookup is not type(key) but isinstance()-like matching.

	e.g.:
	```
	isinstance_getitem(
	    {
	        ast.And: "and",
	        ast.Or: "or",
	    },
	    ast.And(),
	)  # -> "and"
	```

	Args:
		dct: A dict with types as keys and any value type.
		key: The key to look up in the dict, will be checked with isinstance() against the keys of the dict.

	Returns:
		The value in the dict corresponding to the first key that matches the given key with isinstance()

	Raises:
		KeyError: If no key in the dict matches the given key with isinstance()
	"""  # ruff: ignore[mixed-spaces-and-tabs]
	for key_t_candidate, value in dct.items():
		if isinstance(key, key_t_candidate):
			return value

	raise KeyError(key)


def isinstance_get[T](dct: dict[type, T], key: object, *, default: T) -> T:
	"""Non efficient getitem but the keylookup is not type(key) but isinstance()-like matching.

	Wraps `isinstance_getitem()` but returns a default value instead of raising KeyError if no key matches.

	See more details in `isinstance_getitem()` docstring.

	Args:
		dct: A dict with types as keys and any value type.
		key: The key to look up in the dict, will be checked with isinstance() against the keys of the dict.
		default: The default value to return if no key matches.

	Returns:
		The value in the dict corresponding to the first key that matches the given key with isinstance(), or the given default value if no key matches.

	"""

	try:
		return isinstance_getitem(dct, key)
	except KeyError:
		return default
