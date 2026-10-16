class ParkFlowError(Exception):
    def __init__(self, message="An error occurred in the ParkFlow system."):
        self.message = message
        super().__init__(self.message)


def _custom_or_default(value, default, template=None):
    if value is None:
        return default
    text = str(value)
    if " " in text or (template is None and text):
        if " " in text:
            return text
        if template is None:
            return text
    if template is None:
        return default
    return template.format(value)


class DuplicateUserError(ParkFlowError):
    def __init__(self, username=None):
        super().__init__(
            _custom_or_default(
                username,
                "User already exists.",
                "User with username '{}' already exists.",
            )
        )


class UserNotFoundError(ParkFlowError):
    def __init__(self, username=None):
        super().__init__(
            _custom_or_default(
                username,
                "User not found.",
                "User with username '{}' not found.",
            )
        )


class NothingToUndoError(ParkFlowError):
    def __init__(self, message="There are no previous actions to undo."):
        super().__init__(message)


class NotSortedError(ParkFlowError):
    def __init__(self, field=None):
        if field is None:
            super().__init__("Operation failed: Input data must be sorted.")
        elif " " in str(field):
            super().__init__(str(field))
        else:
            super().__init__(
                f"Operation failed: The dataset is not sorted ascending by field '{field}'."
            )


class InvalidPlateError(ParkFlowError):
    def __init__(self, plate=None):
        super().__init__(
            _custom_or_default(
                plate,
                "Invalid license plate format.",
                "Invalid license plate format: '{}'. Must be 3 to 8 alphanumeric characters.",
            )
        )


class InvalidVehicleTypeError(ParkFlowError):
    def __init__(self, v_type=None):
        super().__init__(
            _custom_or_default(
                v_type,
                "Invalid vehicle type provided.",
                "Invalid vehicle type: '{}'. Allowed types are: car, motorcycle, truck.",
            )
        )


class SlotOccupiedError(ParkFlowError):
    def __init__(self, floor=None, slot=None):
        if floor is not None and slot is not None:
            super().__init__(f"Parking slot ({floor}, {slot}) is already occupied.")
        else:
            super().__init__("The selected parking slot is already occupied.")


class SlotEmptyError(ParkFlowError):
    def __init__(self, floor=None, slot=None):
        if floor is not None and slot is not None:
            super().__init__(f"Parking slot ({floor}, {slot}) is already empty.")
        else:
            super().__init__("The selected parking slot is already empty.")


class VehicleAlreadyParkedError(ParkFlowError):
    def __init__(self, plate=None):
        super().__init__(
            _custom_or_default(
                plate,
                "This vehicle is already parked.",
                "Vehicle with plate '{}' is already parked in the facility.",
            )
        )


class DuplicateVehicleError(VehicleAlreadyParkedError):
    pass


class VehicleNotParkedError(ParkFlowError):
    def __init__(self, plate=None):
        super().__init__(
            _custom_or_default(
                plate,
                "Vehicle is not currently parked.",
                "Vehicle with plate '{}' is not found in the active parking records.",
            )
        )


class VehicleNotFoundError(VehicleNotParkedError):
    pass


class WaitingListFullError(ParkFlowError):
    def __init__(self, max_limit=None):
        if max_limit is None:
            super().__init__("Waiting list has reached its maximum capacity.")
        elif isinstance(max_limit, str) and " " in max_limit:
            super().__init__(max_limit)
        else:
            super().__init__(
                f"Waiting list is full (maximum capacity: {max_limit}). Cannot accept more vehicles."
            )


class AuthenticationError(ParkFlowError):
    def __init__(self, username=None):
        super().__init__(
            _custom_or_default(
                username,
                "Authentication failed. Invalid credentials.",
                "Authentication failed for user: '{}'.",
            )
        )


class ReservationError(ParkFlowError):
    def __init__(self, reason=""):
        if reason:
            text = str(reason)
            if text.lower().startswith("reservation error"):
                super().__init__(text)
            else:
                super().__init__(f"Reservation error: {text}")
        else:
            super().__init__("Unable to complete the parking space reservation.")


class InvalidStateError(ParkFlowError):
    def __init__(self, message="The parking lot is in an invalid state."):
        super().__init__(message)


class UndoNotAllowedError(ParkFlowError):
    def __init__(self, message="This action cannot be undone."):
        super().__init__(message)
