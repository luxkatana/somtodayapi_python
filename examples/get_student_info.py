import somtodaypython.nonasyncsomtoday as somtodaypython
from os import getenv

SCHOOL_NAME = getenv("SCHOOL_NAME")
STUDENT_NAME = getenv("STUDENT_NAME")
STUDENT_PASSWORD = getenv("STUDENT_PASSWORD")

school = somtodaypython.find_school(SCHOOL_NAME)

student = school.get_student(STUDENT_NAME, STUDENT_PASSWORD)


print(f"Leerling's naam: {student.full_name}")
print(f"School naam: {student.school_name}")
print(f"Gender: {student.gender}")
print(f"Geregistreerde email: {student.email}")
print("Geboortedatum:", student.birth_datetime.strftime("%d-%m-%Y"))
