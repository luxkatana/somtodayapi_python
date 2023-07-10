import unittest
import somtodaypython
from datetime import datetime, timedelta
nonasync = somtodaypython.nonasyncsomtoday
asynchronoussom = somtodaypython.asynchronous_somtoday


now = datetime.now()
class RoosterTest(unittest.TestCase):
    async def test_asyncrooster(self):
        school = await asynchronoussom.find_school("")
        student = await school.get_student('', '')
        schedule = await student.fetch_schedule(now, now + timedelta(days=2), True)
        print("Asynchronous result -> ", schedule)
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
