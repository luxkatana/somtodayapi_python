'''
Module that provide non-asynchronous functions for using the somtoday API

'''
import base64
from typing import Any
from datetime import datetime
import hashlib
import os
import random
import string
from urllib.parse import urlparse, parse_qs
import requests


class Subject:
    '''
    Subject:
    a model what represents a single school subject/hour
    THIS IS NOT MEANT TO BE CREATED BY THE USER
    '''

    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.subject_name: str = kwargs.get("subject")
        self.begin_time: datetime = kwargs.get("begindt")
        self.end_time: datetime = kwargs.get("enddt")
        self.subject_short: str = kwargs.get("subject_short")
        self.begin_hour: int = kwargs.get("beginhour")
        self.end_hour:  int = kwargs.get("endhour")
        self.location: str = kwargs.get("location")
        self.teacher_short: str = kwargs.get("teacher_shortcut")

    def __repr__(self):
        return f"{self.subject_name}"

    def __str__(self):
        return self.__repr__()


class Student:
    '''
    Student:
        Model that represents a Student
        THIS IS NOT MEANT TO BE CREATED BY THE USER
    '''
    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs.get("name")
        self.password: str = kwargs.get("password")
        self.school_uuid: str = kwargs.get("uuid")
        self.school_name: str = kwargs.get("literal_school")
        self.auth_code: str = kwargs.get("auth_code")
        self.access_token: str = kwargs.get("access")
        self.refresh_token: str = kwargs.get("refresh")
        self.school_subjects: list[Subject] | list[list[Subject]] = []
        self.email: str
        self.full_name: str
        self.gender: str
        self.user_id: int
        self.indentifier: int
        self.birth_datetime: datetime
        self.endpoint = "https://api.somtoday.nl"
        self.load_more_data()

    def fetch_schedule(self,
                        begindt: datetime,
                       enddt: datetime,
                       group_by_day: bool = False) -> list[Subject] | list[list[Subject]]:
        """description: fetches the timetable and saves it to self.school_subjects
        Args:
            begindt (datetime): starting date to fetch
            enddt (datetime):   ending date to fetch
            group_by_day (bool, optional): to group it  by day. Defaults to False.

        Returns:
            list[Subject]  | list[list[Subject]]:  list what contains Subjects or a grouped Subjects
        """
        params_payload = {
            "begindatum": f"{begindt.year}-{begindt.month}-{begindt.day}",
            "einddatum": f"{enddt.year}-{enddt.month}-{enddt.day}",
            "additional": ["vak", "docentAfkortingen"],
            "sort": "asc-beginDatumTijd"
        }
        with requests.get(f"{self.endpoint}/rest/v1/afspraken",
                          headers={"Accept": "application/json",
                                   "Authorization": f"Bearer {self.access_token}"},
                          params=params_payload,
                          timeout=30) as response:
            as_json = response.json()
            items: list[dict] = as_json["items"]
            self.school_subjects = []
            groups: dict[str, list[Subject]] = {}
            for item in items:
                school_object_dict: dict = item.get(
                    "additionalObjects").get("vak")
                afkorting = school_object_dict.get("afkorting")
                subject_name: str = school_object_dict.get("naam")
                locatie: str = item.get("locatie")
                begin_lesuur: int = item.get("beginLesuur")
                eind_lesuur: int = item.get("eindLesuur")
                docent_afkorting: str = item.get(
                    "additionalObjects").get("docentAfkortingen")
                begin_time: datetime = datetime.fromisoformat(
                    item.get("beginDatumTijd"))
                end_time: datetime = datetime.fromisoformat(
                    item.get("eindDatumTijd"))
                target_object = Subject(subject=subject_name,
                                        begindt=begin_time,
                                        enddt=end_time,
                                        subject_short=afkorting,
                                        beginhour=begin_lesuur,
                                        endhour=eind_lesuur,
                                        location=locatie,
                                        teacher_shortcut=docent_afkorting)
                if group_by_day and begin_time.strftime("%Y-%m-%d") in groups:
                    group = groups.get(
                        f"{begin_time.year}-{begin_time.month}-{begin_time.day}")
                    group.append(target_object)
                elif group_by_day and begin_time.strftime("%Y-%m-%d")  not in groups:
                    new_group = {
                        f"{begin_time.year}-{begin_time.month}-{begin_time.day}": [target_object,]
                    }
                    groups.update(new_group)
                else:
                    self.school_subjects.append(target_object)
            if group_by_day:
                self.school_subjects = [groups.get(x) for x in groups]
            return self.school_subjects

    def __repr__(self):
        return f"{self.full_name}, {self.school_name}"

    def __str__(self):
        return self.__repr__()

    def load_more_data(self) -> bool:
        """description: generates data(not meant to be called)

        Returns:
            bool: if it fetched and loaded data by success.
        """
        if hasattr(self, "full_name"):
            return False
        else:
            with requests.get(f"{self.endpoint}/rest/v1/leerlingen",
                              headers={
                                  "Authorization":
                                      f"Bearer {self.access_token}",
                                      "Accept": "application/json"},
                              timeout=30)as name_response:
                to_dict = name_response.json()["items"][0]
                self.full_name = to_dict.get(
                    "roepnaam") + " " + to_dict.get("achternaam")
                self.user_id = to_dict.get("links")[0]["id"]
                self.email = to_dict.get("email")
                self.indentifier = to_dict.get("leerlingnummer")
                self.gender = "Male" if to_dict.get(
                    "geslacht") == "Man" else "Female"
                year, month, day = to_dict.get("geboortedatum").split("-")
                self.birth_datetime = datetime(int(year), int(month), int(day))
        return True

    @property
    def school_object(self) -> "School":
        """description: The school object self(School)

        Returns:
            School: The School where the student has been fetched.
        """
        return School(self.school_name, self.school_uuid)


class School:
    '''
    Model that represents a school.
    NOT MEANT TO BE CREATED BY THE USER
    '''

    def __init__(self, school_name: str, uuid: str) -> None:
        self.school_name = school_name
        self.school_uuid = uuid
        self.__failed_time = 0

    @staticmethod
    def from_school_uuid(uuid: str) -> "School":
        """description: Creates a School object from a tenant_uuid(uuid)
        Args:
            uuid (str):  The uuid from the school

        Raises:
            ValueError: uuid is incorrect

        Returns:
            School: The school what it found
        """
        with requests.get("https://servers.somtoday.nl/organisaties.json",
                          timeout=30)as school_response:
            as_dict = school_response.json()
            instellingen = as_dict[0]["instellingen"]
            exists = tuple(filter(lambda school_: school_[
                           "uuid"] == uuid, instellingen))
            if exists:
                return School(exists[0]["naam"], uuid)
            else:
                raise ValueError(f"Invalid  uuid: {uuid}")

    @staticmethod
    def from_school_name(name: str) -> "School":
        """description: Alternative to find_school()

        Args:
            name (str): The school's name
        Returns:
            School: The School self
        """
        return find_school(name)

    def get_student(self, name: str, password: str) -> Student:
        """description: Get's the student by name and password(currently the only method)
        Args:
            name (str):  The student's name
            password (str):  The student's password

        Raises:
            ValueError: Credentials are incorrect.
            requests.exceptions.RequestException: Error at  last https request. Rarely happens.

        Returns:
            Student: The student self.
        """
        if self.__failed_time > 10:
            raise ValueError("Credentials might be invalid. Please check")
        cookies_saved: list | str = []
        token = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
        hashed = base64.urlsafe_b64encode(hashlib.sha256(
            token.encode()).digest()).rstrip(b'=').decode()
        payload = {
            "response_type": "code",
            "redirect_uri": "somtodayleerling://oauth/callback",
            "code_challenge": hashed,
            "tenant_uuid": self.school_uuid,
            "code_challenge_method": "S256",
            "state": "".join(random.choices(string.ascii_letters, k=20)),
            "scope": "openid",
            "client_id": "D50E0C06-32D1-4B41-A137-A9A850C892C2",
            "session": "no_session"

        }
        response = requests.get(
            "https://inloggen.somtoday.nl/oauth2/authorize",
            params=payload,
            allow_redirects=False,
            timeout=30)
        cookies_saved = response.cookies
        parsed = urlparse(response.headers.get("location"))
        auth_token = parse_qs(parsed.query).get("auth")[0]

        post_headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://inloggen.somtoday.nl"
        }
        firstpos = requests.post("https://inloggen.somtoday.nl/", data={
            "loginLink": "x",
            "usernameFieldPanel:usernameFieldPanel_body:usernameField": name
        }, params={"-1.-panel-signInForm": "",
                   "auth": auth_token},
            headers=post_headers, allow_redirects=False, cookies=cookies_saved, timeout=30)

        cookies_saved = firstpos.cookies
        secondpos = requests.post(
            "https://inloggen.somtoday.nl/login",
            data={
                "loginLink": "x",
                "passwordFieldPanel:passwordFieldPanel_body:passwordField": password
            },
            headers=post_headers,
            params={
                "1-1.-passwordForm": "",
                "auth": auth_token
            },
            cookies=cookies_saved,
            allow_redirects=False,
            timeout=30
        )
        location2 = secondpos.headers.get('location')
        code_as_return: str = None
        if location2.startswith("somtodayleerling:"):
            parsed_url = urlparse(location2)
            code_as_return: str = parse_qs(parsed_url.query).get("code")[0]
        else:
            thirdpost = requests.post(
                "https://inloggen.somtoday.nl/login",
                data={
                    "loginLink": "x",
                    "passwordFieldPanel:passwordFieldPanel_body:passwordField": password
                },
                headers=post_headers,
                params={
                    "1-1.-passwordForm": "",
                    "auth": auth_token
                },
                cookies=cookies_saved,
                allow_redirects=False,
                timeout=30
            )
            location3 = thirdpost.headers.get("location")
            if location3.startswith("somtodayleerling:"):
                parsed_url = urlparse(location3)
                code_as_return: str = parse_qs(parsed_url.query).get("code")[0]
            else:
                self.__failed_time += 1
                return self.get_student(name, password)
        last_response_payload = {
            "grant_type":  "authorization_code",
            "scope": "openid",
            "client_id": "D50E0C06-32D1-4B41-A137-A9A850C892C2",
            "tenant_uuid": self.school_uuid,
            "session": "no_session",
            "code": code_as_return,
            "code_verifier":  token
        }
        last_response_headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        last_response_final_response_ara_ara = requests.post(
            "https://inloggen.somtoday.nl/oauth2/token", data=last_response_payload,
            headers=last_response_headers,
            timeout=30)
        if last_response_final_response_ara_ara.status_code == 200:
            to_dict = last_response_final_response_ara_ara.json()
            return Student(name=name,
                           password=password,
                           uuid=self.school_uuid,
                           literal_school=self.school_name,
                           auth_code=auth_token,
                           access=to_dict["access_token"],
                           refresh=to_dict["refresh_token"])
        else:
            raise requests.exceptions.RequestException(
                f"request failed. request code {last_response_final_response_ara_ara.status_code}")


def find_school(school_name: str) -> School | None:
    """description: Function that returns a school by name

    Args:
        school_name (str): The school's name

    Raises:
        ValueError: The school's name is incorrect.

    Returns:
        School | None: The school  itself
    """
    with requests.get("https://servers.somtoday.nl/organisaties.json", timeout=30)as schoolresponse:
        response_as_dict = schoolresponse.json()
        final_result = tuple(filter(lambda school_dict: school_dict["naam"].lower(
        ) == school_name.lower(), response_as_dict[0]["instellingen"]))
        if final_result:
            return School(school_name, final_result[0]["uuid"])
        else:
            raise ValueError(f"{school_name} does not exist")
