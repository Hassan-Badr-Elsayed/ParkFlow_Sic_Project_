import re

from core.exceptions import InvalidPlateError, InvalidVehicleTypeError


def normalize_plate(plate):
    if not plate or not isinstance(plate, str):
        raise InvalidPlateError(plate)

    clean = re.sub(r"[\s\-]+", "", plate).upper()

    if not re.match(r"^[A-Z0-9]{3,8}$", clean):
        raise InvalidPlateError(plate)

    return clean


def validate_vehicle_type(v_type):
    if not v_type or not isinstance(v_type, str):
        raise InvalidVehicleTypeError(v_type)

    v_type_clean = v_type.strip().lower()
    allowed = ["car", "motorcycle", "truck"]

    if v_type_clean not in allowed:
        raise InvalidVehicleTypeError(v_type)

    return v_type_clean
