import enum

from .conftest import π_t


class Enum_(enum.Enum):
	FOO = enum.auto()
	BAR = enum.auto()
	BAZ = enum.auto()


class StrEnum_(enum.StrEnum):
	FOO = "foo"
	BAR = "bar"
	BAZ = "baz"


class Flag_(enum.Flag):
	FOO = enum.auto()
	BAR = enum.auto()
	BAZ = enum.auto()


class IntFlag_(enum.IntFlag):
	FOO = 1 << 0
	BAR = 1 << 1
	BAZ = 1 << 2


def test_enum(π: π_t):
	π << Enum_.FOO
	print()
	π << StrEnum_.BAR
	print()
	π << Flag_.FOO
	π << (Flag_.FOO | Flag_.BAZ)
	print()
	π << IntFlag_.FOO
	π << (IntFlag_.FOO | IntFlag_.BAZ)
	π.hr()
	π << Enum_
	π << StrEnum_
	π << Flag_
	π << IntFlag_


def test_hikari_enum(π: π_t):
	try:
		import hikari
	except ImportError:
		π.comment("!!! `hikari` module not available, skipping this test")
		return

	π << hikari.invites.TargetType.EMBEDDED_APPLICATION
	print()
	π << hikari.MessageFlag.EPHEMERAL
	π << (hikari.MessageFlag.EPHEMERAL | hikari.MessageFlag.IS_COMPONENTS_V2)
	print()
	π << hikari.invites.TargetType
	π << hikari.MessageFlag
