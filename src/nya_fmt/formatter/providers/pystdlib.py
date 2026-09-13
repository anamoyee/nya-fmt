from __future__ import annotations

import abc
import ast
import datetime as dt
import enum
import inspect
import itertools as it
import re
from ast import Call
from collections.abc import Generator, Iterable, Iterator, Mapping, MutableMapping
from math import isinf, isnan
from pathlib import Path, PurePath
from types import EllipsisType, FunctionType, ModuleType
from typing import TYPE_CHECKING, Any, Literal, TypeAliasType, TypeGuard, assert_never

import astpretty
from nya_result import Maybe
from rich.text import Text

from ..displayers.raw import DisplayRawText
from . import _util
from ._base import FormatProviderABC as FPABC

if TYPE_CHECKING:
	from .._base import Formatter

try:
	import hikari.internal.enums
except ImportError:
	hikari_available = False
else:
	hikari_available = True


class FP__builtins__bool(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, bool):
			return Maybe.new_none()

		return Maybe.new_some(
			Text(
				f"{v!r}",
				style=(fmt.styles.true if v else fmt.styles.false),
			)
		)


class FP__builtins__None(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if v is not None:
			return Maybe.new_none()

		return Maybe.new_some(
			Text(
				f"{v!r}",
				style=fmt.styles.none,
			)
		)


class FP__builtins__int(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, int):
			return Maybe.new_none()

		text = Text(
			f"{v:{fmt.int_format_specifier}}",
			style=fmt.styles.number,
		)

		text.highlight_words("+-", fmt.styles.punctuation)

		return Maybe.new_some(text)


class FP__builtins__float(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, float):
			return Maybe.new_none()

		float_str = f"{v:{fmt.float_format_specifier}}"

		if fmt.float_use_infinity_symbol:
			float_str = float_str.replace("inf", "∞")

		text = Text(
			float_str,
			style=fmt.styles.number,
		)

		text.highlight_words(".+-eE", fmt.styles.punctuation)

		if isnan(v) or isinf(v):
			with fmt.with_tmp_settings():
				fmt.prefer_short_name = True
				type_text = fmt(type(v))

			return Maybe.new_some(type_text + fmt._fh__raw_in_parens(text))

		return Maybe.new_some(text)


class FP__pathlib__PurePath(
	FPABC
):  # todo: Make it look like `eza` colored formatting (e.g. aqua for dirs, red for broken symlinks, maybe reuse same color for non existent paths, or maybe use gray for nonexistent idk, etc.)
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, PurePath):
			return Maybe.new_none()

		str_text = fmt(v.as_posix())
		str_text.highlight_regex("/", fmt.styles.punctuation)

		p_text = Text("P" if v.__class__.__name__.startswith("Pure") else "p", style=fmt.styles.letter_p_Path)

		return Maybe.new_some(p_text + str_text)


class _FPABC__collections__Iterable(FPABC, no_auto_register=True):
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

	@property
	def is_len1_skipping_indent(self) -> bool:
		return True

	@abc.abstractmethod
	def accept(self, v: object) -> TypeGuard[Iterable[object]]: ...

	def iter_has_more_items(self, v: Iterator[object], /) -> bool:
		try:
			next(iter(v))
		except StopIteration:
			return False
		else:
			return True

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not self.accept(v):
			return Maybe.new_none()

		try:
			len_v: int | None = len(v)  # type: ignore
		except TypeError:
			len_v = None

		v_iter = iter(v)
		v_isliced_list = list(it.islice(v_iter, fmt.iterable_max_display_len))

		n_more: int | Literal["?"]
		if len_v is None:
			if self.iter_has_more_items(v_iter):
				n_more = "?"
			else:
				n_more = 0
		else:
			n_more = len_v - len(v_isliced_list)

		opening, closing = self.brackets(fmt=fmt)

		comma = self.comma(fmt=fmt)

		if len_v == 0:
			return Maybe.new_some(opening + (comma if self.is_len0_comma_added else Text()) + closing)

		if self.is_len1_skipping_indent and len_v == 1:
			return Maybe.new_some(opening + fmt(*v) + (comma if self.is_len1_comma_added else Text()) + closing)

		newline_if_indent_not_none = Text("\n" if fmt.indent is not None else "")
		space_if_indent_none = Text(" " if fmt.indent is None else "")
		comma_if_indent_not_none = comma if fmt.indent is not None else Text()

		return Maybe.new_some(
			Text().join((
				opening,
				newline_if_indent_not_none,
				(comma + newline_if_indent_not_none + space_if_indent_none).join(
					fmt.add_indent(x)  #
					for x in it.chain(
						(fmt(v_item) for v_item in v_isliced_list),
						(
							(
								Text().join((
									Text("*", style=fmt.styles.operator),
									fmt._fh__raw_in_parens(
										Text(f"<{n_more} more...>", style=fmt.styles.iterable_max_display_len_overflow),
									),
								)),
							)
							if n_more != 0
							else ()
						),
					)
				),
				comma_if_indent_not_none,
				newline_if_indent_not_none,
				closing,
			))
		)


class _FPABC__collections__Mapping(_FPABC__collections__Iterable, no_auto_register=True):
	def colon(self, *, fmt: Formatter) -> Text:
		return fmt._fh__colon()

	@property
	def is_len0_comma_added(self) -> bool:
		return False

	@property
	def is_len1_comma_added(self) -> bool:
		return False

	@abc.abstractmethod
	def accept(self, v: object) -> TypeGuard[Mapping[object, object]]: ...

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not self.accept(v):
			return Maybe.new_none()

		try:
			len_v = len(v)
		except TypeError:
			v = dict(v.items())
			len_v = len(v)

		opening, closing = self.brackets(fmt=fmt)

		comma = self.comma(fmt=fmt)

		if len_v == 0:
			return Maybe.new_some(opening + (comma if self.is_len0_comma_added else Text()) + closing)

		if self.is_len1_skipping_indent and len_v == 1:
			return Maybe.new_some(
				Text().join((
					opening,
					fmt(*v.keys()),
					fmt._fh__colon(),
					fmt._fh__space(),
					fmt(*v.values()),
					(comma if self.is_len1_comma_added else Text()),
					closing,
				))
			)

		newline_if_indent_not_none = Text("\n" if fmt.indent is not None else "")
		space_if_indent_none = Text(" " if fmt.indent is None else "")
		comma_if_indent_not_none = comma if fmt.indent is not None else Text()

		return Maybe.new_some(
			Text().join((
				opening,
				newline_if_indent_not_none,
				(comma + newline_if_indent_not_none + space_if_indent_none).join(
					fmt.add_indent(x)  #
					for x in it.chain(
						it.islice(
							(
								fmt(k) + self.colon(fmt=fmt) + " " + fmt(v)  #
								for k, v in v.items()
							),
							fmt.iterable_max_display_len,
						),
						(
							Text().join((
								Text("**", style=fmt.styles.operator),  #
								fmt._fh__raw_in_parens(
									Text(f"<{len(v) - (fmt.iterable_max_display_len)} more...>", style=fmt.styles.iterable_max_display_len_overflow),
								),
							)),
						)
						if len(v) > fmt.iterable_max_display_len
						else (),
					)
				),
				comma_if_indent_not_none,
				newline_if_indent_not_none,
				closing,
			))
		)


class FP__builtins__tuple(_FPABC__collections__Iterable):
	@property
	def is_len1_comma_added(self) -> bool:
		return True

	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("(", style=fmt.styles.bracket),
			Text(")", style=fmt.styles.bracket),
		)

	def accept(self, v: object) -> TypeGuard[tuple]:
		return isinstance(v, tuple)


class FP__builtins__list(_FPABC__collections__Iterable):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("[", style=fmt.styles.bracket),
			Text("]", style=fmt.styles.bracket),
		)

	def accept(self, v: object) -> TypeGuard[list]:
		return isinstance(v, list)


class FP__collections__Generator(_FPABC__collections__Iterable):
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

	def accept(self, v: object) -> TypeGuard[Generator]:
		return inspect.isgenerator(v)


class FP__builtins__set(_FPABC__collections__Iterable):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	@property
	def is_len0_comma_added(self) -> bool:
		return True

	def accept(self, v: object) -> TypeGuard[set]:
		return isinstance(v, set)


class FP__builtins__frozenset(_FPABC__collections__Iterable):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("F", style=fmt.styles.letter_F_frozenset) + Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	@property
	def is_len0_comma_added(self) -> bool:
		return True

	def accept(self, v: object) -> TypeGuard[frozenset]:
		return isinstance(v, frozenset)


class FP__collections__MutableMapping(_FPABC__collections__Mapping):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	def accept(self, v: object) -> TypeGuard[MutableMapping[object, object]]:
		return isinstance(v, (MutableMapping, dict))


class FP__collections__Mapping(_FPABC__collections__Mapping):
	def brackets(self, *, fmt: Formatter) -> tuple[Text, Text]:
		return (
			Text("{", style=fmt.styles.bracket),
			Text("}", style=fmt.styles.bracket),
		)

	def accept(self, v: object) -> TypeGuard[Mapping[object, object]]:
		return isinstance(v, Mapping)


class FP__builtins__type(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, type):
			return Maybe.new_none()

		text = Text(
			fmt._fh__get_full_name_of_type(v),
			style=fmt.styles.type,
		)

		text.highlight_regex(r"\.", fmt.styles.punctuation)

		return Maybe.new_some(text)


class FP__builtins__Ellipsis(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, EllipsisType):
			return Maybe.new_none()

		return Maybe.new_some(Text("...", style=fmt.styles.punctuation))


class FP__ast__expr_VIA_unparse(FPABC, no_auto_register=True):
	def _format_ast_arguments_as_call(self, args: ast.arguments, *, fmt: Formatter) -> Text:
		return Text("<ast.argumments>")  # todo: impl

	def _impl_comprehension_body(self, el: ast.expr | tuple[ast.expr, ast.expr], /, *generators: ast.comprehension, fmt: Formatter) -> Text:
		if isinstance(el, tuple):
			el_k, el_v = el
			fmted_el = fmt(el_k) + fmt._fh__colon() + fmt._fh__space() + fmt(el_v)
		else:
			fmted_el = fmt(el)

		return Text().join((
			fmted_el,
			*(
				Text().join((
					Text(" "),
					Text("async for" if gen.is_async else "for", style=fmt.styles.keyword),
					Text(" "),
					fmt(gen.target),
					Text(" "),
					Text("in", style=fmt.styles.keyword),
					Text(" "),
					fmt(gen.iter),
					*(
						Text().join((
							Text(" "),
							Text("if", style=fmt.styles.keyword),
							Text(" "),
							fmt(if_),
						))
						for if_ in gen.ifs
					),
				))
				for gen in generators
			),
		))

	def _impl(self, v: ast.expr, *, fmt: Formatter) -> Text:
		match v:
			case ast.Constant(value=value):
				return fmt(value)
			case ast.Call(func=name, args=args, keywords=keywords):
				kwargs = {keyword.arg or "": keyword.value for keyword in keywords}
				return fmt(name) + fmt._fh__call(*args, **kwargs)
			case ast.Name(id=id):
				return Text(id, style=fmt.styles.unknown_attribute)
			case ast.Attribute(value=target, attr=attr):
				# todo: later, we can try to detect stuff like ALL_UPPERCASE and try to interpret as an enum.
				return fmt(target) + Text(".", style=fmt.styles.punctuation) + Text(attr, style=fmt.styles.unknown_attribute)
			case ast.Set(elts=xs):
				return fmt._fh__raw_in_curlys(
					(fmt._fh__comma() + fmt._fh__space()).join(
						fmt(x)  #
						for x in xs
					)
				)
			case ast.Subscript(value=target, slice=slice_):
				return fmt(target) + Text("[", style=fmt.styles.bracket) + fmt(slice_) + Text("]", style=fmt.styles.bracket)
			case ast.Dict(keys=keys, values=values):
				return fmt._fh__raw_in_curlys(
					(fmt._fh__comma() + fmt._fh__space()).join(
						Text().join((
							Text("**", style=fmt.styles.operator),
							fmt(v),
						))
						if k is None
						else Text().join((
							fmt(k),
							fmt._fh__colon(),
							fmt._fh__space(),
							fmt(v),
						))
						for k, v in zip(keys, values, strict=True)
					),
				)
			case ast.List(elts=elements):
				return fmt(elements)
			case ast.Tuple(elts=elements):
				return fmt(tuple(elements))
			case ast.UnaryOp(op=op, operand=operand):
				op_str = _util.isinstance_getitem(
					{
						ast.Not: "not",
						ast.UAdd: "+",
						ast.USub: "-",
						ast.Invert: "~",
					},
					op,
				)

				match op:
					case ast.Not():
						text = Text().join((
							Text(op_str, style=fmt.styles.operator),
							Text(" "),
							fmt(operand),
						))

						match fmt._inflight_stack:
							case [*_, ast.UnaryOp(op=ast.Not()), _]:
								pass  # do not apply parens to `not not x` (as in NO: `not (not x)`)
							case [*_, ast.UnaryOp() | ast.BinOp(), _]:
								text = fmt._fh__raw_in_parens(text)

						return text
					case ast.UAdd() | ast.USub() | ast.Invert():
						return Text(op_str, style=fmt.styles.operator) + fmt(operand)
					case _:
						try:
							assert_never(v)  # type: ignore
						except AssertionError as e:
							e.add_note(f"{v=!r}")
							raise

			case ast.BinOp(left=lhs, op=op, right=rhs):
				op_str = _util.isinstance_getitem(
					{
						ast.Add: "+",
						ast.Sub: "-",
						ast.Mult: "*",
						ast.Div: "/",
						ast.FloorDiv: "//",
						ast.Mod: "%",
						ast.Pow: "**",
						ast.LShift: "<<",
						ast.RShift: ">>",
						ast.BitOr: "|",
						ast.BitXor: "^",
						ast.BitAnd: "&",
					},
					op,
				)

				return fmt(lhs) + fmt._fh__space() + Text(op_str, style=fmt.styles.operator) + fmt._fh__space() + fmt(rhs)
			case ast.BoolOp(op=op, values=values):
				match values:
					case [] | [_]:
						msg = "BoolOp with only one or zero values is invalid"
						raise AssertionError(msg)

				op_str = _util.isinstance_getitem(
					{
						ast.And: "and",
						ast.Or: "or",
					},
					op,
				)

				return (Text(f" {op_str} ", style=fmt.styles.operator)).join(fmt(value) for value in values)
			case ast.NamedExpr(target=target, value=value):
				return fmt._fh__raw_in_parens(
					Text().join((
						fmt(target),
						Text(" := ", style=fmt.styles.operator),
						fmt(value),
					))
				)
			case ast.Lambda(args=args, body=body):
				return fmt._fh__raw_in_parens(
					Text().join((
						Text("lambda", style=fmt.styles.keyword),
						fmt._fh__colon(),
						fmt._fh__space(),
						self._format_ast_arguments_as_call(args, fmt=fmt),
						fmt._fh__colon(),
						fmt._fh__space(),
						fmt(body),
					))
				)
			case ast.IfExp(test=test, body=body, orelse=orelse):
				return fmt._fh__raw_in_parens(
					Text().join((
						fmt(body),
						fmt._fh__space(),
						Text("if", style=fmt.styles.keyword),
						fmt._fh__space(),
						fmt(test),
						fmt._fh__space(),
						Text("else", style=fmt.styles.keyword),
						fmt._fh__space(),
						fmt(orelse),
					))
				)
			case (
				ast.ListComp(elt=el, generators=generators)
				| ast.SetComp(elt=el, generators=generators)
				| ast.GeneratorExp(elt=el, generators=generators)
			):
				wrap_in_brackets_fn = _util.isinstance_getitem(
					{
						ast.ListComp: fmt._fh__raw_in_brackets,
						ast.SetComp: fmt._fh__raw_in_curlys,
						ast.GeneratorExp: fmt._fh__raw_in_parens,
					},
					v,
				)

				return wrap_in_brackets_fn(self._impl_comprehension_body(el, *generators, fmt=fmt))
			case ast.DictComp(key=key, value=value, generators=generators):
				return fmt._fh__raw_in_curlys(
					self._impl_comprehension_body((key, value), *generators, fmt=fmt),
				)
			case ast.Await(value):
				return fmt._fh__raw_in_parens(
					Text("await ", style=fmt.styles.keyword) + fmt(value),
				)
			case ast.Yield(value):
				if value is None:
					return fmt._fh__raw_in_parens(
						Text("yield", style=fmt.styles.keyword),
					)

				return fmt._fh__raw_in_parens(
					Text("yield ", style=fmt.styles.keyword) + fmt(value),
				)
			case ast.YieldFrom(value):
				return fmt._fh__raw_in_parens(
					Text("yield from ", style=fmt.styles.keyword) + fmt(value),
				)
			case ast.Compare(left=lhs, ops=ops, comparators=comparators):
				if len(ops) != len(comparators):
					msg = "Compare node has different number of ops and comparators"
					raise AssertionError(msg)

				return fmt._fh__raw_in_parens(
					Text().join((
						fmt(lhs),
						*(
							(
								Text().join((
									fmt._fh__space(),  #
									Text(
										_util.isinstance_getitem(
											{
												ast.Eq: "==",
												ast.NotEq: "!=",
												ast.Lt: "<",
												ast.LtE: "<=",
												ast.Gt: ">",
												ast.GtE: ">=",
												ast.Is: "is",
												ast.IsNot: "is not",
												ast.In: "in",
												ast.NotIn: "not in",
											},
											op,
										),
										style=fmt.styles.operator,
									),
									fmt._fh__space(),
									fmt(comparator),
								))
							)
							for op, comparator in zip(ops, comparators, strict=True)
						),
					))
				)
			case ast.Slice(lower=lower, upper=upper, step=step):
				return fmt(slice(lower, upper, step))
			# case ast.JoinedStr(values):
			# 	msg_0 = "JoinedStr formatting is not implemented yet"
			# 	raise NotImplementedError(msg_0)
			case ast.Starred(value):
				return Text("*", style=fmt.styles.operator) + fmt(value)
			case _:
				try:
					assert_never(v)  # type: ignore # todo: implement all cases, do not remove this assert_never as this guards againast new features in the new python versions + this type: ignore actually is required as mypy/ty is not that smart
				except AssertionError as e:
					e.add_note(f"{v=!r}")
					raise

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, ast.expr):
			return Maybe.new_none()

		text = self._impl(v, fmt=fmt)
		return Maybe.new_some(text)


class FP__ast__expr_VIA_astpretty_into_unparse(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, ast.expr):
			return Maybe.new_none()

		with fmt.with_tmp_settings():
			fmt.ensure_provider_types_missing(type(self))
			fmt.ensure_providers_present(FP__ast__expr_VIA_unparse())

			return Maybe.new_some(
				fmt(
					ast.parse(
						astpretty.pformat(
							v,
							indent=4,
							show_offsets=False,
						),
						mode="eval",
					).body
				)
			)


class FP__builtins__object(FPABC, priority=-1000):
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
		from ..types import HexInt

		if not fmt.include_memory_addresses_in_unknown_objects:
			return fmt._fh__call()

		return fmt._fh__call() + Text(" @", style=fmt.styles.punctuation) + fmt(HexInt(ptr))

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
						fmt.ensure_providers_present(FP__ast__expr_VIA_unparse())
						return fmt._fh__guess_question_mark() + fmt._fh__call(*args, **kwargs)

			with fmt.with_tmp_settings():
				fmt.ensure_providers_present(FP__ast__expr_VIA_unparse())
				repr_v_text = fmt(expr)
		elif (name := fmt._fh__get_partial_name_of_type(v.__class__)) and repr_v.startswith(f"{name}(") and repr_v.endswith(")"):
			middle = repr_v[len(name) + 1 : -1]
			repr_v_text = Text(middle, style="reset")
		else:
			repr_v_text = Text(repr_v, style="reset")

		return Text().join((
			fmt._fh__guess_question_mark(),
			fmt._fh__raw_in_parens(
				repr_v_text,
			),
		))

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		return Maybe.new_some(
			self._make_name_text(v, fmt=fmt) + self._make_call_text(v, fmt=fmt),
		)


class FP__types__FunctionType_VIA_module_path(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
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


class FP__types__FunctionType_VIA_def(FPABC, no_auto_register=True):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, FunctionType):
			return Maybe.new_none()

		try:
			source = inspect.getsource(v)
		except (OSError, TypeError):
			return Maybe.new_none()
			# todo: try to disassemble the __code__ if finding source impossible, later move it to FP__types__FunctionType_VIA_dis

		return Maybe.new_some(
			fmt._fh__add_indentlike_prefix(
				Text(source, style="red"),
				prefix=Text("|   ", style=fmt.styles.punctuation),
			)
		)


class FP__builtins__str(FPABC):
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
				r"\x00": r"\0",
				r"\x07": r"\a",
				r"\x08": r"\b",
				r"\x09": r"\t",
				r"\x0a": r"\n",
				r"\x0b": r"\v",
				r"\x0c": r"\f",
				r"\x0d": r"\r",
			}

			backslashes = m.group(1)
			esc = m.group(2)

			return backslashes + lookup.get(esc, esc)

		return re.sub(r"(?<!\\)((?:\\\\)*)(\\x[0-9A-Fa-f]{2})", repl, content)

	@staticmethod
	def repr(
		v: str,
		*,
		fmt: Formatter,
	) -> tuple[str, str, str]:
		"""Return the quote character(or multi-character), content, and unquote character(or multi-character) of the string representation of `v`."""

		quote, *content_lst, unquote = repr(v)
		assert quote == unquote

		content = "".join(content_lst)

		if fmt.allow_triple_quotes_for_newlines:
			unquote_newlines_pattern = re.compile(r"(?<!\\)((?:\\\\)*)\\n", re.UNICODE)

			content, count = re.subn(
				unquote_newlines_pattern,
				r"\1\n",
				content,
			)

			if count:
				unquote_tabs_pattern = re.compile(r"(?<!\\)((?:\\\\)*)\\t", re.UNICODE)
				# when the setting `allow_triple_quotes_for_newlines`, is enabled, we also unquote tabs in strings that contain a newline

				content = re.sub(
					unquote_tabs_pattern,
					rf"\1{fmt.indent or "\t"}",
					content,
				)

				quote = unquote = quote * 3

		if (
			len(quote) == 1  # not yet done by previous triple-quote checker.
			and fmt.allow_triple_quotes_for_less_escaping  #
			and quote in content
			and (quote * 3 not in content)
			and (quote * 3).replace("'", '"') not in content
		):
			quote = unquote = quote * 3

		if (
			fmt.doublequotes_preference is not False  # if False, will short-circuit and keep single quotes no matter the string contents
			and (
				fmt.doublequotes_preference  # if True, will succeed no matter the string contents
				or (("'" * len(quote)) in content or ('"' * len(quote)) not in content)
				# if None, will succeed only if the string contains single quotes or no double quotes
			)
		):
			quote = unquote = quote.replace("'", '"')

			while re.search(rf"(?<!\\){re.escape(quote)}", content, re.UNICODE):
				content = content.replace(quote, f"\\{quote}")  # also works for quote='"""'

			unquote_single_quotes_pattern = re.compile(r"(?<!\\)((?:\\\\)*)\\\'", re.UNICODE)
			"""https://regex101.com/r/feqlSI/1/substitution"""
			content = re.sub(unquote_single_quotes_pattern, r"\1'", content)

		return quote, content, unquote

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, str):
			return Maybe.new_none()

		if not fmt.no_quoteless_str and re.fullmatch(r"[a-zA-Z0-9_]+", v):
			return Maybe.new_some(Text(v, style=fmt.styles.string))

		quote, content, unquote = self.repr(
			v,
			fmt=fmt,
		)

		content = self._content_replace_u00_to_x(content)
		content = self._content_replace_x_via_lookup(content)

		if "\n" in content:
			if "\n\n" in content and content.index("\n") == content.index("\n\n"):
				# if the first line is followed by an empty line, keep that line right after the opening quote.
				content = f"{content}\n"
				newline_compensation_slice = slice(None, -1)
			else:
				content = f"\n{content}\n"
				newline_compensation_slice = slice(1, -1)

			# rely on further if `'\n' in content` to append a visual [1:-1] at the end

		content_text = Text(
			content,
			style=fmt.styles.string,
		)

		content_text.highlight_regex(r"(?<!\\)(?:\\\\)*(?:\\[tnrfbv'\"\\]|\\x[0-9A-Fa-f]{2})", fmt.styles.punctuation)

		output_text = Text().join((
			Text(quote, style=fmt.styles.punctuation),
			content_text,
			Text(unquote, style=fmt.styles.punctuation),
		))

		if "\n" in content:
			output_text = Text().join((
				Text("textwrap", fmt.styles.type),
				fmt._fh__dot(),
				Text("dedent", fmt.styles.function),
				fmt._fh__raw_in_parens(
					Text().join((
						output_text,
						fmt._fh__raw_in_brackets(fmt(newline_compensation_slice)),
					))
				),
			))

		return Maybe.new_some(output_text)


class FP__builtins__BaseException(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, BaseException):
			return Maybe.new_none()

		return Maybe.new_some(fmt(type(v)) + fmt._fh__call(*v.args))


class FP__dataclasses__dataclass(FPABC):  # todo: implement attrs & attr in a simillar way
	@staticmethod
	def all_same_type(iterable: Iterable) -> bool:
		iterator = iter(iterable)
		try:
			first_type = type(next(iterator))
		except StopIteration:
			return True  # An empty iterable technically has "all items" matching

		# Check the rest of the items against the first type
		return all(type(item) is first_type for item in iterator)

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not hasattr(v, "__dataclass_fields__"):
			return Maybe.new_none()

		fields: dict[str, Any] = {
			_f_name: _f_value  #
			for _f_name, _f_value in v.__dataclass_fields__.items()  # ty: ignore[unresolved-attribute]
			if getattr(_f_value, "repr", True)
		}

		with fmt.with_tmp_settings():
			fmt.prefer_short_name = True
			name_text = fmt(v.__class__)

		at_dataclass_text = Text("@dataclass ", style=fmt.styles.function)

		field_values = {field_name: getattr(v, field_name) for field_name in fields}

		if (
			fmt.align_dataclass_field_keys_if_all_values_of_same_type  #
			and self.all_same_type(field_values.values())
		):
			key_align_length = max((len(field_name) for field_name in fields), default=0)
		else:
			key_align_length = 0

		return Maybe.new_some(
			(at_dataclass_text if fmt.include_at_notation else Text())
			+ name_text
			+ fmt._fh__call(**{
				f"{field_name:{fmt.dataclass_key_align_char[:1]}<{key_align_length}}": field_values[field_name]  #
				for field_name in fields
			})
		)


class FP__types__ModuleType(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, ModuleType):
			return Maybe.new_none()

		kwargs = dict()

		try:
			v_file = v.__file__

			if v_file is None:
				msg = "__file__ is None"
				raise ValueError(msg)  # ruff:ignore[raise-within-try]

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


class FP__typing__TypeAliasType(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
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


class FP__datetime__date(FPABC):
	# NOTE/WARNING: DO NOT IMPLEMENT IT AS A CLASS HIERARCHY, JUST KEEP COMPOSITION
	# BECAUSE THIS IS A RABBIT HOLE WHICH TIMEZONES RELATED ISSUES WILL FUCK YOU UP SO MUCH NOT TO ESCAPE OUT OF
	@staticmethod
	def is_elapsed(v: dt.date) -> bool:
		return v < dt.datetime.now(tz=dt.UTC).date()

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, dt.date):
			return Maybe.new_none()

		if isinstance(v, dt.datetime):
			return Maybe.new_none()

		bracket_color = fmt.styles.punctuation if not self.is_elapsed(v) else fmt.styles.none

		text = Text().join((
			Text("<"),
			Text(f"{v:{fmt.date_format_specifier}}", style=fmt.styles.number),
			Text(">"),
		))

		text.highlight_words(["<", ">", ":", ",", "-", "."], style=bracket_color)

		return Maybe.new_some(text)


class FP__datetime__time(FPABC):
	# NOTE/WARNING: DO NOT IMPLEMENT IT AS A CLASS HIERARCHY, JUST KEEP COMPOSITION
	# BECAUSE THIS IS A RABBIT HOLE WHICH TIMEZONES RELATED ISSUES WILL FUCK YOU UP SO MUCH NOT TO ESCAPE OUT OF
	@staticmethod
	def time_total_seconds(t: dt.time) -> float:
		return (t.hour * 3600) + (t.minute * 60) + t.second + (t.microsecond / 1_000_000)

	@staticmethod
	def is_elapsed(v: dt.time) -> bool:
		# add tolerance of 1 second
		now_time = dt.datetime.now(tz=v.tzinfo).time()

		v_seconds = FP__datetime__time.time_total_seconds(v)
		now_seconds = FP__datetime__time.time_total_seconds(now_time)

		return v_seconds < (now_seconds - 1)

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, dt.time):
			return Maybe.new_none()

		bracket_color = fmt.styles.punctuation if not self.is_elapsed(v) else fmt.styles.none

		text = Text().join((
			Text("<"),
			Text(f"{v:{fmt.time_format_specifier}}", style=fmt.styles.number),
			Text(">"),
		))

		text.highlight_words(["<", ">", ":", ",", "-", "."], style=bracket_color)

		return Maybe.new_some(text)


class FP__datetime__datetime(FPABC):
	# NOTE/WARNING: DO NOT IMPLEMENT IT AS A CLASS HIERARCHY, JUST KEEP COMPOSITION
	# BECAUSE THIS IS A RABBIT HOLE WHICH TIMEZONES RELATED ISSUES WILL FUCK YOU UP SO MUCH NOT TO ESCAPE OUT OF
	@staticmethod
	def is_elapsed(v: dt.datetime) -> bool:
		# add tolerance of 1 second
		return v < (dt.datetime.now(tz=v.tzinfo) - dt.timedelta(seconds=1))

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, dt.datetime):
			return Maybe.new_none()

		bracket_color = fmt.styles.punctuation if not self.is_elapsed(v) else fmt.styles.none

		text = Text().join((
			Text("<"),
			Text(f"{v:{fmt.date_format_specifier}}", style=fmt.styles.number),
			Text(" "),
			Text(f"{v:{fmt.time_format_specifier}}", style=fmt.styles.number),
			Text(">"),
		))

		text.highlight_words(["<", ">", ":", ",", "-", "."], style=bracket_color)

		return Maybe.new_some(text)


class FP__builtins__slice(FPABC):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not isinstance(v, slice):
			return Maybe.new_none()

		if any(isinstance(fp, FP__ast__expr_VIA_unparse) for fp in fmt.providers):
			slice_d = {"start": v.start, "stop": v.stop, "step": v.step}
			match v.start:
				case ast.Constant(value=None):
					slice_d["start"] = None
			match v.stop:
				case ast.Constant(value=None):
					slice_d["stop"] = None
			match v.step:
				case ast.Constant(value=None):
					slice_d["step"] = None
			v = slice(slice_d["start"], slice_d["stop"], slice_d["step"])

		disambiguation_parens_required = True
		match (v.start, v.stop, v.step):
			case (
				int() | None | ast.Constant(value=int()),
				int() | None | ast.Constant(value=int()),
				int() | None | ast.Constant(value=int()),
			):
				disambiguation_parens_required = False

		left_colon = False
		right_colon = False

		if v.start is not None and v.stop is not None:  # start:stop*
			left_colon = True
		if v.stop is not None and v.step is not None:  # *stop:step
			right_colon = True
		if v.start is not None and v.step is not None:  # start:*:step
			left_colon = True
			right_colon = True
		if all(x is None for x in (v.start, v.stop, v.step)):  # : (empty slice)
			left_colon = True

		if not any((left_colon, right_colon)):  #
			left_colon = True
		if right_colon:
			left_colon = True

		text = Text().join((
			fmt(v.start) if v.start is not None else Text(),
			fmt._fh__colon() if left_colon else Text(),
			fmt(v.stop) if v.stop is not None else Text(),
			fmt._fh__colon() if right_colon else Text(),
			fmt(v.step) if v.step is not None else Text(),
		))

		if disambiguation_parens_required:
			text = fmt._fh__raw_in_parens(text)

		return Maybe.new_some(text)


class FP__enum__Enum(FPABC, priority=10):
	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not (
			(
				hikari_available
				and (
					isinstance(v, hikari.internal.enums.Enum)  #  # ruff: ignore[duplicate-isinstance-call]
					or isinstance(v, hikari.internal.enums.Flag)
				)
			)  #
			or isinstance(v, enum.Enum)
		):
			return Maybe.new_none()

		progression_found = FP__enum__typeof_Enum.has_any_progression(v.__class__)

		v_name_text = Text(v.name, style=fmt.styles.enum_member)
		v_name_text.highlight_words(["|"], style=fmt.styles.punctuation_muted)

		with fmt.with_tmp_settings():
			fmt.ensure_provider_types_missing(FP__enum__typeof_Enum)
			fmted_v_class_without_typeof_Enum_fp = fmt(v.__class__)

		return Maybe.new_some(
			Text().join((
				fmted_v_class_without_typeof_Enum_fp,
				Text(".", style=fmt.styles.punctuation_muted),
				v_name_text,
				*(
					()
					if progression_found
					else (
						Text(": ", style=fmt.styles.punctuation_muted),
						fmt(v.value),
					)
				),
			))
		)


class FP__enum__typeof_Enum(FPABC, priority=10):
	@staticmethod
	def has_linear_progression(v_t: type[enum.Enum], /, *, start: int) -> bool:
		try:
			for i, v_item in enumerate(v_t, start=start):
				if i != v_item.value:
					return False
		except Exception:
			return False

		return True

	@staticmethod
	def has_geometric_progression(v_t: type[enum.Enum], /, *, start: int) -> bool:
		try:
			i = start
			for v_item in v_t:
				if v_item.value != i:
					return False

				if i == 0:
					i = 1
				else:
					i *= 2
		except Exception:
			return False

		return True

	@staticmethod
	def has_any_progression(v_t: type[enum.Enum], /) -> bool:
		return (
			FP__enum__typeof_Enum.has_linear_progression(v_t, start=0)  #
			or FP__enum__typeof_Enum.has_linear_progression(v_t, start=1)
			or FP__enum__typeof_Enum.has_geometric_progression(v_t, start=0)
			or FP__enum__typeof_Enum.has_geometric_progression(v_t, start=1)
		)

	def try_fmt(self, v: object, /, *, fmt: Formatter) -> Maybe[Text]:
		if not (
			(
				hikari_available
				and isinstance(v, type)
				and (
					issubclass(v, hikari.internal.enums.Enum)  #
					or issubclass(v, hikari.internal.enums.Flag)
				)
			)  #
			or (isinstance(v, type) and issubclass(v, enum.Enum))
		):
			return Maybe.new_none()

		with fmt.with_tmp_settings():
			fmt.ensure_provider_types_missing(type(self))
			fmted_v_without_self_fp = fmt(v)

		progression_detected = FP__enum__typeof_Enum.has_any_progression(v)

		return Maybe.new_some(
			Text().join((
				fmted_v_without_self_fp,
				Text("Meta", style=fmt.styles.word_Meta_enum),
				fmt._fh__call(
					{
						DisplayRawText(Text(x.name, style=fmt.styles.enum_member))  #
						for x in v
					}
					if progression_detected
					else {
						DisplayRawText(Text(x.name, style=fmt.styles.enum_member)): x.value  #
						for x in v
					}
				),
			))
		)
