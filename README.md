***Somtoday Python, the interactor***


> What the f**ck is this?

this(somtoday python) is a package that fetches and interacts with somtoday API using https requests.

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
***examples***

*basic interacting with a student(getting data from the student)*
```py

import somtodaypython.nonasyncsomtoday as nonasync_somtoday
school = nonasync_somtoday.find_school("SchoolName")
student = school.get_student("NAME", "password")
print(f"email : {student.email}\tname: {student.full_name}\tgender: {student.full_name}")
```
*basic interacting with the timetable of a student*
```py
import somtodaypython.nonasyncsomtoday as nonasync_somtoday
from datetime import datetime as dt
school = nonasync_somtoday.find_school("SchoolName")
student = school.get_student("NAME", "password")
today = dt.now()
tomorrow = dt(today.year, today.month, today.day + 2) # it will skip the secondth day
timetable: list[list[nonasync_somtoday.Subject]] = student.fetch_schedule(today, tomorrow, group_by_day=True)
for day in timetable:
    for day_subject in day:
        print(day_subect.name)
```

**Asynchronous suppport**

We also support asynchronous for somtodaypython.

*Basic interacting with a student(asynchronous)*
```py
import somtodaypython.asynchronous_somtoday as async_somtoday
import  asyncio # builtin library for asynchronous execution
async def main() -> None:
    school = await async_somtoday.find_school("SCHOOLNAME")
    student = await school.get_student("NAME", "PASSWORD")
    print(student.full_name)
asyncio.get_event_loop().run_until_complete(main()) # executing the main() function
```

*Basic interacting with a student's timetable(asynchronous)*

```py

import somtodaypython.asynchronous_somtoday as async_somtoday
from datetime import datetime as dt
import  asyncio # builtin library for asynchronous execution
async def main() -> None:
    now = dt.now()
    tomorrow = dt(now.year, now.month, now.day  + 2)
    school = await async_somtoday.find_school("SCHOOLNAME")
    student = await school.get_student("NAME", "PASSWORD")
    timetable: list[list[async_somtoday.Subject]] = await student.fetch_schedule(now, tomorrow, group_by_day=True)
    for day in timetable:
        for  subject in day:
            print(subject.name)
asyncio.get_event_loop().run_until_complete(main()) # executing the main() function
```


**Ending**


New features are always welcome! email taseen.bibi@gmail.com


**Huizengek#6623**
Special thanks to **Huizengek#6623** for showing the method of getting the access token & interacting with the somtoday API.

github: https://github.com/25huizengek1


**elisaado**

Special thanks to **elisaado** for making important API endpoints visible to other users.

github: https://github.com/elisaado/somtoday-api-docs