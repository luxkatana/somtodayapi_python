import unittest
import somtodaypython.nonasyncsomtoday as nonasyncsomtoday
from os import getenv

SCHOOL = getenv('SCHOOL')
NAAM: str = str(getenv("NAAM"))
PASSWORD: str = getenv("PASSWORD")
school: nonasyncsomtoday.School = nonasyncsomtoday.find_school(SCHOOL)
student = school.get_student(NAAM, PASSWORD)


class CijferComparison(unittest.TestCase):
    def test_cijferyielding(self):
        for  cijfer in student.yield_fetch_cijfers(1, 10):
            print(cijfer)

    def test_main(self):
        cijfers = student.fetch_cijfers(1, 10)
        if len(cijfers) >= 2:
            cijfer1  = cijfers[0]
            cijfer2 = cijfers[1]
            if cijfer1 > cijfer2:
                print(f"Je staat op {cijfer1.vak} hoger dan op {cijfer2.vak}")
            elif cijfer1 < cijfer2:
                print(f"Je staat op {cijfer1.vak} lager dan op {cijfer2.vak}")
            else:
                print(f"Je cijfer voor {cijfer1.vak} is hetzelfde als {cijfer2.vak}")


if __name__ == '__main__':
    unittest.main()
