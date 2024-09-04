***Somtoday Python, the interactor***

***Changed my mind, somtodaypython is back alive***

***A big revamp has been made, I am planning to add SSO authentication.***


***asynchronous support for somtodaypython has been deprecated***


somtodaypython is a package that fetches and interacts with Somtoday API using HTTPS requests.

**installation**

*for macos & linux*
```
python3 -m pip3 install somtodaypython 
```
*for windows*
```
python3 -m pip install somtodaypython 
```
OR
```
python -m pip install somtodaypython
```

if neither above works then you can always do this
```
pip3 install git+https://github.com/luxkatana/somtodayapi_python
```

***examples***

*basic interacting with a student(getting data from the student)*
```py

import somtodaypython.nonasyncsomtoday as nonasync_somtoday
school = nonasync_somtoday.find_school("SchoolName")
student = school.get_student("NAME", "password")
print(f"email : {student.email}\tname: {student.full_name}\tgender: {student.gender}")
```
*basic interacting with the timetable of a student*
```py
import somtodaypython.nonasyncsomtoday as nonasync_somtoday
from datetime import timedelta, datetime as dt
school = nonasync_somtoday.find_school("SchoolName")
student = school.get_student("NAME", "password")
today = dt.now()
tomorrow = today + timedelta(days=2)
timetable: list[list[nonasync_somtoday.Subject]] = student.fetch_schedule(today, tomorrow, group_by_day=True)
for day in timetable:
    for day_subject in day:
        print(day_subject.subject_name)
```

**Contribution**


New PR's are welcome.


**Huizengek#6623**
Special thanks to **Huizengek#6623** for showing the method of getting the access token & interacting with the somtoday API.

github: https://github.com/25huizengek1


**elisaado**

Special thanks to **elisaado** for making important API endpoints visible to other users.

github: https://github.com/elisaado/somtoday-api-docs
