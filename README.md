***Somtoday Python, the interactor***

***changes in 0.0.4***
<ul>
<li> I got more lazier so I wanted to do announce this in Dutch </li>
<li> Gefixt dat Student.fetch_schedule(group_by_day=True) dat het weer werkt(zat blijkbaar een bug in) </li>
<li> Documentatie verbetert </li>
<li> Er zat een probleem met Union types, gefixt </li>
<li> Je kan 2 studenten vergelijken als Student.full_name en Student.school_name allebei gelijk zijn
<li> Vergelijkingen met Cijfers(kijken als cijfers zijn hoger of lager) Cijfers worden bepaald door Cijfers.resultaat
<li>beter __repr__ en __str__ voor Cijfer en Subject</li>
</ul>


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
        print(day_subect.subject_name)
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
from datetime import timedelta,datetime as dt
import  asyncio # builtin library for asynchronous execution
async def main() -> None:
    now = dt.now()
    tomorrow = now + timedelta(days=2)
    school = await async_somtoday.find_school("SCHOOLNAME")
    student = await school.get_student("NAME", "PASSWORD")
    timetable: list[list[async_somtoday.Subject]] = await student.fetch_schedule(now, tomorrow, group_by_day=True)
    for day in timetable:
        for  subject in day:
            print(subject.subject_name)
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
