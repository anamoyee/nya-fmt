from __future__ import annotations

import abc
import ast
import inspect
import json
import os
import re
from ast import Call
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from shlex import join
from types import EllipsisType, FunctionType, ModuleType
from typing import TYPE_CHECKING, Any, TypeAliasType, assert_never

from nya_result import Maybe
from rich.text import Text

from ._base import FormatProviderABC as FPABC

if TYPE_CHECKING:
	from .._base import Formatter


class BoolFP(FPABC[bool]):
	def try_fmt(self, v: bool | Any, /, *, fmt: Formatter) -> Maybe[Text]:  # noqa: FBT001
		if not isinstance(v, bool):
			return Maybe.new_none()

		return Maybe.new_some(
			Text(
				f"{v!r}",
				style=(fmt.styles.true if v else fmt.styles.false),
			)
		)


class NoneFP(FPABC[None]):
	def try_fmt(self, v: None | Any, /, *, fmt: Formatter) -> Maybe[Text]:  # noqa: RUF036
		if v is not None:
			return Maybe.new_none()

		return Maybe.new_some(
			Text(
				f"{v!r}",
				style=fmt.styles.none,
			)
		)


class IntFP(FPABC[int]):
	def try_fmt(self, v: int | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, int):
			return Maybe.new_none()

		text = Text(
			f"{v!r}",
			style=fmt.styles.number,
		)

		text.highlight_regex(r"-", fmt.styles.punctuation)

		return Maybe.new_some(text)


class FloatFP(FPABC[float]):
	def try_fmt(self, v: float | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, float):
			return Maybe.new_none()

		text = Text(
			f"{v:{fmt.float_format_specifier}}",
			style=fmt.styles.number,
		)

		text.highlight_regex(r"-", fmt.styles.punctuation)
		text.highlight_regex(r"(?i)e(?:\+|-)?", fmt.styles.punctuation)
		text.highlight_regex(r"\.", fmt.styles.punctuation)

		return Maybe.new_some(text)


class PurePathFP(FPABC[PurePath]):
	if os.name == "nt":

		def _path_str(self, v: PureWindowsPath) -> str:
			return str(v.as_posix())

	else:

		def _path_str(self, v: PurePosixPath) -> str:
			return str(v)

	def try_fmt(self, v: PurePath | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, PurePath):
			return Maybe.new_none()

		str_text = fmt(self._path_str(v))
		str_text.highlight_regex("/", fmt.styles.punctuation)

		p_text = Text("P" if v.__class__.__name__.startswith("Pure") else "p", style=fmt.styles.letter_p_Path)

		return Maybe.new_some(p_text + str_text)


class _IterableFPABC(FPABC[Iterable], no_auto_register=True):
	@abc.abstractmethod
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]: ...

	def comma(self, *, fmt: Formatter) -> Text:
		return fmt._fh__comma()

	@property
	def is_len0_comma_added(self) -> bool:
		return False

	@property
	def is_len1_comma_added(self) -> bool:
		return False

	@abc.abstractmethod
	def accept(self, v: Iterable) -> bool: ...

	def try_fmt(self, v: Iterable, /, *, fmt: Formatter) -> Maybe[Text]:
		if not self.accept(v):
			return Maybe.new_none()

		try:
			len_v = len(v)  # type: ignore
		except TypeError:
			v = list(v)
			len_v = len(v)

		opening, closing = self.brackets(fmt=fmt)

		comma = self.comma(fmt=fmt)

		if len_v == 0:
			return Maybe.new_some(opening + (comma if self.is_len0_comma_added else Text()) + closing)

		if len_v == 1:
			return Maybe.new_some(opening + fmt(*v) + (comma if self.is_len1_comma_added else Text()) + closing)

		newline_if_indent_not_none = Text("\n" if fmt.indent is not None else "")
		space_if_indent_none = Text(" " if fmt.indent is None else "")
		comma_if_indent_not_none = comma if fmt.indent is not None else Text()

		return Maybe.new_some(
			Text().join((
				opening,
				newline_if_indent_not_none,
				(comma + newline_if_indent_not_none + space_if_indent_none).join(
					fmt.add_indent(fmt(x))  #
					for x in v
				),
				comma_if_indent_not_none,
				newline_if_indent_not_none,
				closing,
			))
		)


class _MappingFPABC(_IterableFPABC, no_auto_register=True):
	def colon(self, *, fmt: Formatter) -> Text:
		return fmt._fh__colon()

	@property
	def is_len0_comma_added(self) -> bool:
		return False

	@property
	def is_len1_comma_added(self) -> bool:
		return False

	@abc.abstractmethod
	def accept(self, v: Iterable) -> bool: ...

	def try_fmt(self, v: Iterable, /, *, fmt: Formatter) -> Maybe[Text]:
		if not self.accept(v):
			return Maybe.new_none()

		try:
			len_v = len(v)  # type: ignore
		except TypeError:
			v = dict(v.items())
			len_v = len(v)

		opening, closing = self.brackets(fmt=fmt)

		comma = self.comma(fmt=fmt)

		if len_v == 0:
			return Maybe.new_some(opening + (comma if self.is_len0_comma_added else Text()) + closing)

		if len_v == 1:
			return Maybe.new_some(opening + fmt(*v) + (comma if self.is_len1_comma_added else Text()) + closing)

		newline_if_indent_not_none = Text("\n" if fmt.indent is not None else "")
		space_if_indent_none = Text(" " if fmt.indent is None else "")
		comma_if_indent_not_none = comma if fmt.indent is not None else Text()

		return Maybe.new_some(
			Text().join((
				opening,
				newline_if_indent_not_none,
				(comma + newline_if_indent_not_none + space_if_indent_none).join(
					fmt.add_indent(fmt(k) + self.colon(fmt=fmt) + " " + fmt(v))  #
					for k, v in v.items()
				),
				comma_if_indent_not_none,
				newline_if_indent_not_none,
				closing,
			))
		)


class TupleFP(_IterableFPABC):
	@property
	def is_len1_comma_added(self) -> bool:
		return True

	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("(", style=fmt.styles.bracket),
			Text(")", style=fmt.styles.bracket),
		)

	def accept(self, v: Iterable) -> bool:
		return isinstance(v, tuple)


class ListFP(_IterableFPABC):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("[", style=fmt.styles.bracket),
			Text("]", style=fmt.styles.bracket),
		)

	def accept(self, v: Iterable) -> bool:
		return isinstance(v, list)


class GeneratorFP(_IterableFPABC):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("<", style=fmt.styles.bracket),
			Text(">", style=fmt.styles.bracket),
		)

	@property
	def is_len0_comma_added(self) -> bool:
		return True

	@property
	def is_len1_comma_added(self) -> bool:
		return True

	def accept(self, v: Iterable) -> bool:
		return inspect.isgenerator(v)


class SetFP(_IterableFPABC):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	@property
	def is_len0_comma_added(self) -> bool:
		return True

	def accept(self, v: Iterable) -> bool:
		return isinstance(v, set)


class FrozensetFP(_IterableFPABC):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("F", style=fmt.styles.letter_F_frozenset) + Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	@property
	def is_len0_comma_added(self) -> bool:
		return True

	def accept(self, v: Iterable) -> bool:
		return isinstance(v, frozenset)


class MutableMappingFP(_MappingFPABC):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	def accept(self, v: Iterable) -> bool:
		return isinstance(v, (MutableMapping, dict))


class MappingFP(_MappingFPABC):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	def accept(self, v: Iterable) -> bool:
		return isinstance(v, Mapping)


class TypeFP(FPABC[type]):
	def try_fmt(self, v: type | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, type):
			return Maybe.new_none()

		text = Text(
			fmt._fh__get_full_name_of_type(v),
			style=fmt.styles.type,
		)

		text.highlight_regex(r"\.", fmt.styles.punctuation)

		return Maybe.new_some(text)


class EllipsisFP(FPABC[EllipsisType]):
	def try_fmt(self, v: EllipsisType | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, EllipsisType):
			return Maybe.new_none()

		return Maybe.new_some(Text("...", style=fmt.styles.punctuation))


class AST_expr_UnparseFP(FPABC[ast.expr], no_auto_register=True):
	def try_fmt(self, v: ast.expr | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, ast.expr):
			return Maybe.new_none()

		match v:
			case ast.Constant(value=value):
				return Maybe.new_some(fmt(value))
			case ast.Call(func=name, args=args, keywords=keywords):
				kwargs = {keyword.arg or "": keyword.value for keyword in keywords}
				return Maybe.new_some(fmt(name) + fmt._fh__call(*args, **kwargs))
			case ast.Name(id=id):
				return Maybe.new_some(Text(id, style=fmt.styles.unknown_attribute))
			case ast.Attribute(value=target, attr=attr):
				return Maybe.new_some(
					# todo: later, we can try to detect stuff like ALL_UPPERCASE and try to interpret as an enum.
					fmt(target) + Text(".", style=fmt.styles.punctuation) + Text(attr, style=fmt.styles.unknown_attribute),
				)
			case ast.Set(elts=xs):
				return Maybe.new_some(
					fmt._fh__raw_in_curlys(
						(fmt._fh__comma() + fmt._fh__space()).join(
							fmt(x)  #
							for x in xs
						)
					)
				)
			case ast.Subscript(value=target, slice=slice_):
				return Maybe.new_some(fmt(target) + Text("[", style=fmt.styles.bracket) + fmt(slice_) + Text("]", style=fmt.styles.bracket))
			case ast.Dict(keys=keys, values=values):
				pairs = dict(zip(keys, values, strict=True))

				return Maybe.new_some(fmt(pairs))

			case _:
				try:
					# todo: implement all ast.expr cases.
					assert_never(v)
				except AssertionError as e:
					e.add_note(f"{v=!r}")
					raise


class AST_expr_DumpFP(FPABC[ast.expr]):
	def try_fmt(self, v: ast.expr | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, ast.expr):
			return Maybe.new_none()

		return Maybe.new_some(Text(ast.dump(v, indent=4), style=fmt.styles.error))


class ObjectFP(FPABC[object], priority=-1000):
	@staticmethod
	def _ast_parse_expr_if_valid_syntax(s: str) -> ast.expr | None:
		try:
			tree = ast.parse(s, mode="eval")
		except (SyntaxError, ValueError, TypeError):
			return None
		else:
			return tree.body

	def _make_name_text(self, v: object, *, fmt: Formatter) -> Text:
		text = fmt(v.__class__)

		text.stylize_before(fmt.styles.none)

		return text

	def _make_x_object_at_y_text(self, *, ptr: int, fmt: Formatter) -> Text:
		if not fmt.include_memory_addresses_in_unknown_objects:
			return fmt._fh__call()

		return fmt._fh__call() + Text(" @ ", style=fmt.styles.punctuation) + Text(f"0x{ptr:012x}", style=fmt.styles.number)

	def _make_call_text(self, v: object, *, fmt: Formatter) -> Text:
		repr_v = repr(v)

		if match := re.fullmatch(r"<(?P<name>.+) object at (?P<ptr>0x[0-9a-fA-F]+)>", repr_v):
			ptr = int(match.group("ptr"), base=0)

			return self._make_x_object_at_y_text(ptr=ptr, fmt=fmt)

		if fmt.try_parse_ast_if_only_repr_available and (expr := self._ast_parse_expr_if_valid_syntax(repr_v)):
			match expr:
				case Call(
					args=args,
					keywords=keywords,
				):
					kwargs = {keyword.arg or "": keyword.value for keyword in keywords}

					with fmt.with_tmp_settings():
						if AST_expr_UnparseFP not in fmt.providers:
							fmt.providers = (AST_expr_UnparseFP(), *fmt.providers)

						return Text("?", style=fmt.styles.guess) + fmt._fh__call(*args, **kwargs)

			with fmt.with_tmp_settings():
				if AST_expr_UnparseFP not in fmt.providers:
					fmt.providers = (AST_expr_UnparseFP(), *fmt.providers)
				repr_v_text = fmt(expr)
		elif (name := fmt._fh__get_partial_name_of_type(v.__class__)) and repr_v.startswith(f"{name}(") and repr_v.endswith(")"):
			middle = repr_v[len(name) + 1 : -1]
			repr_v_text = Text(middle, style="reset")  # type: ignore
		else:
			repr_v_text = Text(repr_v, style="reset")

		return Text().join((
			Text("?", style=fmt.styles.guess),
			fmt._fh__raw_in_parens(
				repr_v_text,
			),
		))

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		return Maybe.new_some(
			self._make_name_text(v, fmt=fmt) + self._make_call_text(v, fmt=fmt),
		)


class FunctionFP(FPABC[Callable[..., Any]]):
	def try_fmt(self, v: Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, FunctionType):
			return Maybe.new_none()

		name = fmt._fh__get_full_name_of_type(v)

		text = Text(
			name,
			style=fmt.styles.type,
		)

		text.highlight_regex(r"\.", fmt.styles.punctuation)
		text.highlight_regex(r"[^\.]+(?!\.)$", fmt.styles.function)
		text.highlight_regex(r"[^\.]+(?=\.<locals>\.)", fmt.styles.function)

		return Maybe.new_some(text)


class StrFP(FPABC[str]):
	@staticmethod
	def _content_replace_u00_to_x(content: str) -> str:
		def repl(m: re.Match) -> str:
			backslashes = m.group(1)
			u_esc = m.group(2)

			return backslashes + "\\x" + u_esc[-2:]

		return re.sub(r"(?<!\\)((?:\\\\)*)(\\u00[0-9A-Fa-f]{2})", repl, content)

	@staticmethod
	def _content_replace_x_via_lookup(content: str) -> str:
		def repl(m: re.Match) -> str:
			lookup = {
				r"\x0c": r"\f",
				r"\x08": r"\b",
				r"\x0b": r"\v",
			}

			backslashes = m.group(1)
			esc = m.group(2)

			return backslashes + lookup.get(esc, esc)

		return re.sub(r"(?<!\\)((?:\\\\)*)(\\x[0-9A-Fa-f]{2})", repl, content)

	def try_fmt(self, v: str | Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, str):
			return Maybe.new_none()

		if not fmt.no_quoteless_str and re.fullmatch(r"[a-zA-Z0-9_]+", v):
			return Maybe.new_some(Text(v, style=fmt.styles.string))

		quote, *content, unquote = json.dumps(v)  # type: ignore

		content = "".join(content)  # type: ignore

		content = self._content_replace_u00_to_x(content)  # type: ignore
		content: str = self._content_replace_x_via_lookup(content)  # type: ignore

		content_text = Text(
			content,  # type: ignore
			style=fmt.styles.string,
		)

		content_text.highlight_regex(r"(?<!\\)(?:\\\\)*(?:\\[tnrfbv'\"\\]|\\x[0-9A-Fa-f]{2})", fmt.styles.punctuation)

		return Maybe.new_some(
			Text().join((
				Text(quote, style=fmt.styles.punctuation),  # type: ignore
				content_text,
				Text(unquote, style=fmt.styles.punctuation),  # type: ignore
			))
		)


class BaseExceptionFP(FPABC[BaseException]):
	def try_fmt(self, v: Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, BaseException):
			return Maybe.new_none()

		return Maybe.new_some(fmt(type(v)) + fmt._fh__call(*v.args))


class DataclassFP(FPABC[object]):
	def try_fmt(self, v: Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not hasattr(v, "__dataclass_fields__"):
			return Maybe.new_none()

		fields: dict[str, Any] = v.__dataclass_fields__

		with fmt.with_tmp_settings():
			fmt.prefer_short_name = True
			name_text = fmt(v.__class__)

		at_dataclass_text = Text("@dataclass ", style=fmt.styles.function)

		return Maybe.new_some(
			(at_dataclass_text if fmt.include_at_notation else Text())
			+ name_text
			+ fmt._fh__call(**{
				field_name: getattr(v, field_name)  #
				for field_name in fields
			})
		)


class ModuleFP(FPABC[ModuleType]):
	def try_fmt(self, v: Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, ModuleType):
			return Maybe.new_none()

		kwargs = dict()

		try:
			v_file = v.__file__

			v_file_path = Path(v_file)
		except (AttributeError, ValueError, TypeError):
			pass
		else:
			kwargs["file"] = v_file_path

		with fmt.with_tmp_settings():
			fmt.indent = None

			return Maybe.new_some(
				fmt(ModuleType)
				+ fmt._fh__call(
					v.__name__,
					**kwargs,
				)
			)


class typing_TypeAliasTypeFP(FPABC[TypeAliasType]):
	def try_fmt(self, v: Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, TypeAliasType):
			return Maybe.new_none()

		return Maybe.new_some(
			fmt(v.__class__)
			+ fmt._fh__raw_in_parens(
				(fmt._fh__colon() + " ").join((
					fmt(str(v)),
					fmt(v.__value__),
				))
			)
		)
