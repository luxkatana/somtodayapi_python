from os import getenv
import somtodaypython.nonasyncsomtoday as somtodaypython
from datetime import datetime, timedelta

SCHOOL_NAME = getenv("SCHOOL_NAME")
STUDENT_NAME = getenv("STUDENT_NAME")
STUDENT_PASSWORD = getenv("STUDENT_PASSWORD")

school = somtodaypython.find_school(SCHOOL_NAME)

student = school.get_student(STUDENT_NAME, STUDENT_PASSWORD)

begin_datetime = datetime.fromisoformat("2025-01-15T10:00:00")
later = begin_datetime + timedelta(days=3)
"""
This'll get the rooster of:
> 2025-01-15
> 2025-01-16
(exclusive the last day)
"""

dagen: list[list[somtodaypython.Subject]] = student.fetch_schedule(
    begin_datetime, later, group_by_day=True
)
"""
group_by_day=True ensures that the rooster of each day is seperated in lists
"""

DAYS = (
    "Maan",
    "Dins",
    "Woens",
    "Donder",
    "Vrij",
    "Zater",
    "Zon",
)  # te lui om alles uit te typen, heb momenteel 3 * 7 = 21 karakters bespaard>:)
for dag in dagen:
    print("Rooster voor {}dag".format(DAYS[dag[0].begin_time.weekday()]))
    for lesuur in dag:
        print(
            "\t{}{} uur is {} van docent(e) {}".format(
                lesuur.begin_hour,
                "ste" if lesuur.begin_hour in (1, 8) else "de",
                lesuur.subject_name,
                lesuur.teacher_short,
            )
        )
