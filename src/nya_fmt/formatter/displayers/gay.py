import itertools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.text import Text

if TYPE_CHECKING:
	from .._base import Fmt


@dataclass
class DisplayAsGay:
	s: str

	style_tuple: tuple[str, ...] = field(
		kw_only=True,
		default=(
			"#FF5555",
			"#FFA500",
			"#FFFF55",
			"#55FF55",
			"#FF55FF",
			"#5555FF",
			"#AF00FF",
			"#5F00FF",
		),
	)

	def __nya_fmt__(self, fmt: "Fmt") -> Text:
		return Text().join(
			Text(char, style=f"b {style_str}")
			for char, style_str in zip(
				self.s,
				itertools.cycle(self.style_tuple),
				strict=False,
			)
		)
