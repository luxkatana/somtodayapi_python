import unittest
import somtodaypython
from datetime import datetime, timedelta
nonasync = somtodaypython.nonasyncsomtoday


now = datetime.now()
class RoosterTest(unittest.TestCase):
    def test_rooster(self):
        school =  nonasync.find_school('')
        student = school.get_student('', '')
        rooster = student.fetch_schedule(
            now,
            now + timedelta(days=2),
            True
        )
        print("Non asynchronous results -> ", rooster)


if __name__ == '__main__':
    unittest.main()
