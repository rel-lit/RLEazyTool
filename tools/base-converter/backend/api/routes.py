"""FastAPI routers for base-converter endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..application import base_service, machine_service, fixed_point_service, floating_point_service, ieee754_service
from ..domain.models import (
    BaseConversionResult,
    MachineNumberResult,
    FixedPointResult,
    FloatingPointResult,
)

router = APIRouter(prefix="/api")


def _handle(func, *args, **kwargs):
    """Catch domain ValueError and return a user-friendly 400 response."""
    try:
        return func(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class BaseConvertRequest(BaseModel):
    value: str
    from_base: int
    to_base: int
    precision: int = 8


class MachineNumberRequest(BaseModel):
    value: str
    width: int = 8
    is_fraction: bool = False
    double_sign: bool = False


class FixedPointRequest(BaseModel):
    x: str
    y: str
    width: int = 8
    double_sign: bool = False
    operation: str = "add"  # "add" or "sub"
    is_fraction: bool = False


class FloatingPointRequest(BaseModel):
    x_mantissa: str
    x_exponent: str
    y_mantissa: str
    y_exponent: str
    operation: str = "add"
    exponent_width: int = 6
    mantissa_width: int = 7


class Ieee754Request(BaseModel):
    value: str
    precision: str = "float32"  # "float32" or "float64"
    direction: str = "to_ieee"  # "to_ieee" or "to_decimal"


@router.post("/convert/base", response_model=BaseConversionResult)
def convert_base(req: BaseConvertRequest):
    return _handle(base_service.convert_base, req.value, req.from_base, req.to_base, req.precision)


@router.post("/convert/machine", response_model=MachineNumberResult)
def convert_machine(req: MachineNumberRequest):
    return _handle(machine_service.convert, req.value, req.width, req.is_fraction, req.double_sign)


@router.post("/compute/fixed", response_model=FixedPointResult)
def compute_fixed(req: FixedPointRequest):
    return _handle(fixed_point_service.add_sub, req.x, req.y, req.width, req.double_sign, req.operation, req.is_fraction)


@router.post("/compute/float", response_model=FloatingPointResult)
def compute_float(req: FloatingPointRequest):
    return _handle(
        floating_point_service.add_sub,
        req.x_mantissa, req.x_exponent, req.y_mantissa, req.y_exponent,
        req.operation, req.exponent_width, req.mantissa_width
    )


@router.post("/convert/ieee754")
def convert_ieee754(req: Ieee754Request):
    return _handle(ieee754_service.convert_float, req.value, req.precision, req.direction)
