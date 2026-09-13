import pydantic

from nya_fmt.formatter.providers.pydantic_ import FP__pydantic__BaseModel_VIA_dict, FP__pydantic__BaseModel_VIA_dict_resolved

from .conftest import π_t


class SmallModel(pydantic.BaseModel):
	a: int = pydantic.Field(default=1, description="This is a field with a default value of 1.")


class InnerModel(pydantic.BaseModel):
	z: int = pydantic.Field(default=3, description="This is a field in the inner model with a description.")
	w: str = pydantic.Field(default="default")


class Model(pydantic.BaseModel):
	x: int = pydantic.Field(default=1)
	y: int = pydantic.Field(default=2)
	mod: InnerModel = pydantic.Field(
		default_factory=InnerModel, description="This is a field with a default factory that returns an instance of InnerModel."
	)
	mod2: SmallModel = pydantic.Field(default_factory=SmallModel)

	field_excluded: str = pydantic.Field(default="excluded", exclude=True)
	field_no_repr: str = pydantic.Field(default="no_repr", repr=False)
	field_excluded_no_repr: str = pydantic.Field(default="excluded_no_repr", exclude=True, repr=False)
	field_exclude_if: str = pydantic.Field(default="exclude_if", exclude_if=lambda v: True)


def test_model1(π: π_t):
	for _ in π.parametrize_providers(
		FP__pydantic__BaseModel_VIA_dict(),
		FP__pydantic__BaseModel_VIA_dict_resolved(),
	):
		π << Model(
			x=1,
			y=2,
			mod=InnerModel(z=3),
		)
