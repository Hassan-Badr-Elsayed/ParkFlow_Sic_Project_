import re
from core.models import Customer, Employee
from core.exceptions import AuthenticationError, DuplicateUserError, InvalidStateError, ParkFlowError, UserNotFoundError
from core.structures import HashTable

HASH_SIZE = 53

class UserManager:
    """Class responsible for handling all user-related validation & authentication."""
    def __init__(self):
        self._users = HashTable(HASH_SIZE)

    @staticmethod
    def _user_key(username):
        return str(username).strip().lower()

    def load_users(self, users):
        fresh = HashTable(HASH_SIZE)
        for user in users:
            key = self._user_key(user.username)
            if fresh.contains(key):
                raise InvalidStateError(f"Duplicate username in data: {user.username}")
            fresh.put(key, user)
        self._users = fresh

    def get_user(self, username):
        return self._users.get(self._user_key(username))

    def get_users(self):
        return list(self._users.values())

    def add_user(self, user):
        self._users.put(self._user_key(user.username), user)

    # 1. Authentication Logic
    def authenticate(self, username, password):
        user = self.get_user(username)
        if user is None:
            raise AuthenticationError("User not found.")
        expected = getattr(user, "password", None) or user.username
        if str(password) != str(expected):
            raise AuthenticationError("Incorrect password.")
        return user

    def _next_user_id(self):
        ids = []
        for user in self._users.values():
            try:
                ids.append(int(user.user_id))
            except (TypeError, ValueError):
                continue
        return str(max(ids) + 1 if ids else 1)

    def create_employee(self, username, email="", password="", user_id=None):
        username = str(username).strip()
        if not username:
            raise InvalidStateError("Employee username cannot be empty.")
        if self._users.contains(self._user_key(username)):
            raise DuplicateUserError(username)
            
        emp = Employee(
            user_id or self._next_user_id(),
            username,
            email or "",
            password=password or username,
        )
        self.add_user(emp)
        return emp

    def delete_employee(self, username):
        user = self.get_user(username)
        if user is None:
            raise UserNotFoundError(username)
        if str(getattr(user, "role", "")).lower() != "employee":
            raise InvalidStateError("Only Gate Operator (Employee) accounts can be deleted here.")
        self._users.remove(self._user_key(username))
        return user

    # 2. Strong Validation & Registration Logic
    def register_customer(self, username, password, phone="", plate="", email=""):
        if not username or len(username) < 3:
            raise ParkFlowError("Username must be at least 3 characters long.")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            raise ParkFlowError("Username can only contain letters, numbers, dots, and underscores.")
            
        if not password or len(password) < 6:
            raise ParkFlowError("Password must be at least 6 characters long.")
            
        
        if phone and not re.match(r"^\d{8,15}$", phone):
            raise ParkFlowError("Phone number must be between 8 and 15 digits.")

        
        if email and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            raise ParkFlowError("Invalid email format (e.g., name@example.com).")
            
        users_list = self.get_users()
        
        if any(u.username.lower() == username.lower() for u in users_list):
            raise ParkFlowError("Username already exists. Please choose a different one.")

        customer_plates = []
        if plate:
            
            cleaned_plate = str(plate).replace("-", "").replace(" ", "").strip().upper()
            if not re.match(r"^[A-Z0-9]{3,8}$", cleaned_plate):
                raise ParkFlowError("Invalid license plate format. Must be 3 to 8 alphanumeric characters.")
            
            for u in users_list:
                if hasattr(u, "plates") and cleaned_plate in u.plates:
                    raise ParkFlowError(f"Plate '{cleaned_plate}' is already registered to another account.")
                    
            customer_plates.append(cleaned_plate)
            
        new_id = str(len(users_list) + 1)
        new_customer = Customer(
            user_id=new_id, 
            username=username.strip(), 
            password=password, 
            email=email.strip(), 
            has_history=False,
            plates=customer_plates
        )
        new_customer.phone = phone.strip() 
        
        self.add_user(new_customer)
        return new_customer

    def add_vehicle_to_customer(self, username, plate):
        import re
        user = self.get_user(username)
        if user is None or str(getattr(user, "role", "")).lower() != "customer":
            raise ParkFlowError("Only registered customers can add vehicles.")
            
        
        cleaned_plate = str(plate).replace("-", "").replace(" ", "").strip().upper()
        if not re.match(r"^[A-Z0-9]{3,8}$", cleaned_plate):
            raise ParkFlowError("Invalid license plate format. Must be 3 to 8 alphanumeric characters.")
            
        for u in self.get_users():
            if hasattr(u, "plates") and cleaned_plate in u.plates:
                raise ParkFlowError(f"Plate '{cleaned_plate}' is already registered to another account.")
                
        if not hasattr(user, "plates"):
            user.plates = []
            
        if cleaned_plate in user.plates:
            raise ParkFlowError(f"Plate '{cleaned_plate}' is already in your account.")
            
        user.plates.append(cleaned_plate)
        return cleaned_plate