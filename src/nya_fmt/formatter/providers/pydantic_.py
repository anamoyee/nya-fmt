from __future__ import annotations

from typing import TYPE_CHECKING

from nya_result import Maybe
from rich.text import Text

from .. import displayers as displayers_m
from ._base import FormatProviderABC as FPABC

if TYPE_CHECKING:
	import pydantic

	from ._base import Fmt


def apply_len1_multiline_dict_recursively(v: dict[object, object], /) -> displayers_m.Len1MultilineDict:
	return displayers_m.Len1MultilineDict({
		k: apply_len1_multiline_dict_recursively(v[k]) if isinstance(v[k], dict) else v[k]  #  # ty: ignore[invalid-argument-type]
		for k in v
	})


class FP__pydantic__BaseModel_VIA_dict(FPABC, no_auto_register=True):
	def try_fmt(self, v: object, /, *, fmt: Fmt) -> Maybe[Text]:
		try:
			import pydantic
		except ImportError:
			return Maybe.new_none()

		if not isinstance(v, pydantic.BaseModel):
			return Maybe.new_none()

		return Maybe.new_some(
			Text().join((
				fmt(type(v)),
				fmt._fh__raw_in_parens(
					Text().join((
						Text("**", style=fmt.styles.operator),
						fmt(
							apply_len1_multiline_dict_recursively(v.model_dump()),
						),
					))
				),
			))
		)


def _UNSAFE_cast_to_model_fields(v) -> dict[str, pydantic.fields.FieldInfo]:  # ruff: ignore[missing-type-function-argument]
	return v


class FP__pydantic__BaseModel_VIA_dict_resolved(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Fmt) -> Maybe[Text]:
		try:
			import pydantic
		except ImportError:
			return Maybe.new_none()

		if not isinstance(v, pydantic.BaseModel):
			return Maybe.new_none()

		return Maybe.new_some(
			Text().join((
				fmt(type(v)),
				fmt._fh__raw_in_parens(
					Text("**", style=fmt.styles.operator)
					+ fmt(
						displayers_m.Len1MultilineDict({
							key: value  #
							for key, field_info in _UNSAFE_cast_to_model_fields(type(v).model_fields).items()
							if (value := getattr(v, key), None)[-1]
							or all([
								field_info.repr,
								not field_info.exclude,
								(field_info.exclude_if is None or not field_info.exclude_if(value)),
							])
						})
					),
				),
			))
		)
