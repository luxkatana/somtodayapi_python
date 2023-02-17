import os
from dotenv import load_dotenv
import requests
load_dotenv()
password = os.environ.get("password")
school = somtodaypython.nonasyncsomtoday.find_school("Hondsrug College")
student = school.get_student(133600, password)
endpoint = student.endpoint
access_token = student.access_token
headers = {
    "Accept": "Application/json",
    "Authorization": f"Bearer {access_token}"
}
params = {
    "additional": ["pasfoto", "leerlingen"]
}
response = requests.get(f"{endpoint}/rest/v1/resultaten/huidigVoorLeerling", headers=headers, params=params)
print(response)
