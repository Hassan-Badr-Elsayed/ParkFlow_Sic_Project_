import unittest
import os

from core.exceptions import ReservationError
from core.models import ParkingSpace, Admin, Employee, Customer
from core.storage import save_records, load_records
from core.validators import normalize_plate

class TestStudent1(unittest.TestCase):

    def test_plate_normalization(self):
        self.assertEqual(normalize_plate(" abc 123 "), "ABC123")

    def test_users_and_roles(self):
        admin = Admin('1', 'boss', 'admin@test.com')
        self.assertEqual(admin.username, 'boss')
        self.assertEqual(admin.role, 'admin')

    def test_parking_space_reservation(self):
        space = ParkingSpace(0, 0)
        self.assertTrue(space.is_free())
        space.reserve("cust_sarah")
        self.assertFalse(space.is_free())

        with self.assertRaises(ReservationError):
            space.reserve("cust_alex")

    def test_save_load_users_round_trip(self):
        test_file = "data/test_users_temp.csv"
        user_data = [
            {'user_id': '1', 'username': 'test_admin', 'role': 'admin', 'email': 'a@a.com', 'has_history': False}
        ]
        fields = ['user_id', 'username', 'role', 'email', 'has_history']
        
        save_records(test_file, user_data, fields)
        loaded = load_records(test_file)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]['username'], 'test_admin')
        
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == '__main__':
    unittest.main()