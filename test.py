import ast
import os
from collections.abc import Callable
from dataclasses import dataclass, field

from rich.text import Text


@(lambda f: f())
def _():
	from rich.traceback import install

	install(
		width=os.get_terminal_size().columns,
	)


import nya_fmt as nf
from nya_fmt import Formatter


def hr():
	print("-" * 20)


fmt = Formatter(
	debug_raise_exceptions=True,
)

fmt << True
fmt << False
fmt << None
hr()

fmt << 1
fmt << 123
fmt << -1
fmt << -123
hr()

fmt << 1.23e10
fmt << -1.23e10
fmt << 1.23e4 + 0.4
fmt << -1.23e4 - 0.4
fmt << 1.23
fmt << -1.23
fmt << 1.23e-4
fmt << -1.23e-4
fmt << 1.23e-8
fmt << -1.23e-8

hr()
fmt << ()
fmt << (1,)
fmt << (((1, 2, 3),),)
fmt << (1, (2, (3,)))
fmt << ((((((((),),),),),),),)

hr()
fmt << []
fmt << [1]
fmt << [[[1, 2, 3]]]
fmt << [1, [2, [3]]]
fmt << [[[[[[[]]]]]]]

hr()
fmt << type
fmt << int
fmt << (lambda: 1)


def f(): ...


def outer() -> Callable[[], Callable[[], None]]:
	def inner() -> Callable[[], None]:
		def innest() -> None:
			pass

		return innest

	return inner


fmt << [
	object(),
	0,
	"",
	"asdfasf",
	"with space",
	"with_special_chars_!@#$%^&*()",
	"with\0fucking\nshitass\twhatever\bchars",
	os.path.join,
	f,
	lambda: None,
	outer,
	outer(),
	outer()(),
	object.__subclasses__,
]

(
	fmt
	<< "asdfv\x00\\\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfeasdfd\xff"
)

fmt << "\t\n\r\f\b\v"
fmt << "'\""
fmt << '"'


class GoodboyNyaFmt:
	def __nya_fmt__(self, fmt: Formatter) -> Text:
		return Text("nya fmted!", style="b orange")


class BadboyNyaFmt:
	def __nya_fmt__(self, fmt: Formatter) -> Text:
		msg = "bad boy >:C"
		raise RuntimeError(msg)


fmt << GoodboyNyaFmt()
with fmt.with_tmp_settings():
	fmt.debug_raise_exceptions = False
	fmt << [BadboyNyaFmt(), 1]
fmt << GoodboyNyaFmt()

hr()
fmt << KeyError(1)
fmt << ValueError("gay")
fmt << RuntimeError()
fmt << BaseException("base exception")

hr()

fmt << fmt


@dataclass
class Dataclass:
	x: int
	y: str = field(default="default")
	z: bool = field(kw_only=True, default=False)


class Class:
	def __init__(self, x: int, y: str = "default", *, z: bool = False):
		self.x = x
		self.y = y
		self.z = z

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}(x={self.x}, y={self.y!r}, z={self.z})"


fmt << Dataclass(1)
fmt << Class(1)

fmt << nf.displayers.DisplayAsGay("anamoyee")
fmt << nf

fmt << ...

hr()

type GayInt = int
type GayGeneric[T] = list[T]

fmt << GayInt
fmt << GayGeneric
fmt << GayGeneric[int]

hr()


class ReprIsStringifiedFirstArgument:
	def __init__(self, __o: object, /) -> None:
		self.__o = __o

	def __repr__(self) -> str:
		return repr(self.__o)


d = {"a": 1, "b": 2, "c": {1, 2, 3}}
fmt << ReprIsStringifiedFirstArgument(d)  # todo: fix the ast.Set repr is different than set's (missing split to newlines)
fmt << d


expr = ast.parse("""(x := 1.3).format(".2f")""", mode="eval")


fmt << expr.body

import astpretty

fmt << astpretty.pformat(expr.body)
