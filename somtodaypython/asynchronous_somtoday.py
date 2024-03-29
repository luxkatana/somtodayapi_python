'''
asynchronous support for somtoday API
'''
import asyncio
import base64
import os
import string
from . import nonasyncsomtoday as nonasync_smtd
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from dataclasses import dataclass
import hashlib
import random
import httpx
from typing import Union


class PasFoto(nonasync_smtd.PasFoto):
    def __init__(self, b64url: str) -> None:
        super().__init__(b64url)


@dataclass

class Cijfer(nonasync_smtd.Cijfer):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


@dataclass

class Subject(nonasync_smtd.Subject):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

class Student(nonasync_smtd.Student):
    '''
    Model that presents a Student
    NOT MEANT TO BE CREATED BY USER
    '''

    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs.get("name")
        self.password: str = kwargs.get("password")
        self.school_uuid: str = kwargs.get("uuid")
        self.school_name: str = kwargs.get("literal_school")
        self.auth_code: str = kwargs.get("auth_code")
        self.access_token: str = kwargs.get("access")
        self.refresh_token: str = kwargs.get("refresh")
        self.school_subjects: list[Union[Subject, list[Subject]]] = []
        self.email: str
        self.full_name: str
        self.gender: str
        self.cijfers: list[Cijfer]
        self.leerlingnummer: int
        self.indentifier: int
        self.birth_datetime: datetime
        self.endpoint = "https://api.somtoday.nl"
        self.pasfoto: PasFoto
        self.dump_cache: dict[str]

    async def yield_fetch_cijfers(self, lower_bound_range: int, upper_bound_range: int):
        """yields the cijfers by calling self.fetch_cijfers() and yielding it results

        Args:
            lower_bound_range (int):  minimum to return (must be greater than 0 and fewer than 100)
            upper_bound_range (int):  maximum to return (must be fewer than 100)

        Yields:
            cijfer: Cijfer object
        """        
        
        cijfers = await self.fetch_cijfers(lower_bound_range, upper_bound_range)
        for cijfer in cijfers:
            yield cijfer


    async def fetch_cijfers(self, lower_bound_range: int, upper_bound_range: int) -> list[Cijfer]:
        """fetches the cijfers and saves it to self.cijfers

        Args:
            lower_bound_range (int): minimum to return must be greater than 0  and fewer than 100
            upper_bound_range (int): maximum to return(must be fewer than 100)
        Raises:
            ValueError: lower_boung_range or upper_boung_range is negative or more than 100
            ExceptionGroup: status code is not what is expected

        Returns:
            list[Cijfer]: list of Cijfers
        """
        if lower_bound_range >= 100 or lower_bound_range <= 0:
            raise ValueError("lower_bound_range can't be negative or more than 100")
        elif upper_bound_range >= 100 or upper_bound_range <= 0:
            raise ValueError("upper_bound_range can't be negative or more than 100")
        headers = {
            "Accept": "Application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Range": f"items={lower_bound_range}-{upper_bound_range}"
        }
        params = {
            "additional": ['berekendRapportCijfer']
        }
        async with httpx.AsyncClient() as session:
            response = await session.get(f"{self.endpoint}/rest/v1/resultaten/huidigVoorLeerling/{self.identifier}",
                                         params=params, headers=headers)
            if response.status_code >= 200 and response.status_code < 300:
                to_dict = response.json()
                items: list[dict] = to_dict["items"]
                self.cijfers = []
                for item in items:
                    tijd_nagekeken = datetime.fromisoformat(item["datumInvoer"])
                    resultaat = item.get("resultaat", "0")
                    leerjaar = item['leerjaar']
                    vak = item["vak"]["naam"]
                    self.cijfers.append(Cijfer(vak=vak, datum=tijd_nagekeken, leerjaar=leerjaar, resultaat=resultaat))
                self.dump_cache = to_dict
                return self.cijfers
            else:
                raise ExceptionGroup("error", [
                    [
                        f"response returned status code {response.status_code} from {self.endpoint}/rest/v1/resultaten/huidigVoorLeerling/{self.identifier}"
                    ]
                ])

    async def yield_fetch_schedule(self,
                             begindt: datetime,
                             enddt: datetime,
                             group_by_day: bool = False):
        """Yielding each ``Subject`` object 

        Args:
            begindt (datetime): starting date to fetch
            enddt (datetime): ending date to fetch
            group_by_day (bool, optional): to group it by day. Defaults to False.

        """        
        schedule = await self.fetch_schedule(begindt, enddt, group_by_day)
        for subject in schedule:
            yield subject
    async def fetch_schedule(self,
                             begindt: datetime,
                             enddt: datetime,
                             group_by_day: bool = False) -> list[Union[list[Subject], Subject]]:
        """description: fetches the timetable and saves it to self.school_subjects
        Args:
            begindt (datetime): starting date to fetch
            enddt (datetime):   ending date to fetch
            group_by_day (bool, optional): to group it  by day. Defaults to False.

        Returns:
            list[Subject]  | list[list[Subject]]:  list that contains Subjects or a grouped Subjects
        """
        params_payload = {
            "begindatum": f"{begindt.year}-{begindt.month}-{begindt.day}",
            "einddatum": f"{enddt.year}-{enddt.month}-{enddt.day}",
            "additional": ["vak", "docentAfkortingen"],
            "sort": "asc-beginDatumTijd"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.endpoint}/rest/v1/afspraken",
                                        headers={"Accept": "application/json",
                                                 "Authorization": f"Bearer {self.access_token}"},
                                        params=params_payload)
            as_json = response.json()
            items: list[dict] = as_json["items"]
            self.school_subjects = []
            groups: dict[str, list[Subject]] = {}
            for item in items:
                school_object_dict: dict = item.get("additionalObjects").get("vak")
                afkorting = school_object_dict.get("afkorting")
                subject_name: str = school_object_dict.get("naam")
                locatie: str = item.get("locatie")
                begin_lesuur: int = item.get("beginLesuur")
                eind_lesuur: int = item.get("eindLesuur")
                docent_afkorting: str = item.get("additionalObjects").get("docentAfkortingen")
                begin_time: datetime = datetime.fromisoformat(item.get("beginDatumTijd"))
                end_time: datetime = datetime.fromisoformat(item.get("eindDatumTijd"))
                target_object = Subject(subject=subject_name,
                                        begindt=begin_time,
                                        enddt=end_time,
                                        subject_short=afkorting,
                                        beginhour=begin_lesuur,
                                        endhour=eind_lesuur,
                                        location=locatie,
                                        teacher_shortcut=docent_afkorting)
                if group_by_day and begin_time.strftime("%Y-%m-%d") in groups:
                    group = groups.get(begin_time.strftime("%Y-%m-%d"))
                    group.append(target_object)
                elif group_by_day and begin_time.strftime("%Y-%m-%d") not in groups:
                    new_group = {
                        begin_time.strftime("%Y-%m-%d"): [target_object]
                    }
                    groups.update(new_group)
                else:
                    self.school_subjects.append(target_object)
            if group_by_day:
                self.school_subjects = [groups.get(x) for x in groups]
            return self.school_subjects


    async def load_more_data(self) -> bool:
        '''
        function that loads data what will be saved by the self object.
        '''
        if hasattr(self, "full_name"):
            return False
        else:
            async with httpx.AsyncClient() as client:
                name_response = await client.get(f"{self.endpoint}/rest/v1/leerlingen",
                                                 headers={
                                                     "Authorization": f"Bearer {self.access_token}",
                                                     "Accept": "application/json"},
                                                 params={"additional": ["pasfoto", "leerlingen"]})
                to_dict = name_response.json()
                to_dict = to_dict["items"][0]
                self.pasfoto = PasFoto(to_dict["additionalObjects"]["pasfoto"]["datauri"])
                self.full_name = to_dict.get("roepnaam") + " " + to_dict.get("achternaam")
                self.identifier = to_dict.get("links")[0]["id"]
                self.email = to_dict.get("email")
                self.leerlingnummer = to_dict.get("leerlingnummer")
                self.gender = "Male" if to_dict.get("geslacht") == "Man" else "Female"
                year, month, day = to_dict.get("geboortedatum").split("-")
                self.birth_datetime = datetime(int(year), int(month), int(day))
            return True


class School(nonasync_smtd.School):
    '''
    Model that represents a school
    NOT  MEANT TO BE CREATED BY USER
    '''

    def __init__(self, *args) -> None:
        super().__init__(*args)

    @staticmethod
    async def from_school_uuid(uuid: str) -> "School":
        """Gets a school by school uuid

        Args:
            uuid (str): the school uuid

        Raises:
            ValueError: school does not exist

        Returns:
            School: object that represents the School
        """
        async with httpx.AsyncClient() as session:
            school_response = await session.get("https://servers.somtoday.nl/organisaties.json")
            as_dict = school_response.json()
            instellingen = as_dict[0]["instellingen"]
            exists = tuple(filter(lambda school_: school_["uuid"] == uuid, instellingen))
            if exists:
                return School(exists[0]["naam"], uuid)
            raise ValueError(f"Invalid  uuid: {uuid}")

    @staticmethod
    async def from_school_name(name: str) -> "School":
        '''
        get the School from_school name, alternative to find_school(name)
        '''
        return await find_school(name)

    async def get_student(self, name: str, password: str) -> Student:
        """description: Gets the student by name and password(without SSO)
        Args:
            name (str):  The student's name - The login name you use to login at inloggen.somtoday.nl
            password (str):  The student's password

        Raises:
            ValueError: Credentials are incorrect.
            requests.exceptions.RequestException: Error at  last https request. Rarely happens.

        Returns:
            Student: The student self.
        """

        if self.__failed_time > 10:
            raise ValueError("Credentials might be invalid. Please check")
        cookies_saved = []
        token = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
        hashed = base64.urlsafe_b64encode(hashlib.sha256(token.encode()).digest()).rstrip(b'=') \
            .decode()
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
        async with httpx.AsyncClient() as client:
            response = await client.get("https://inloggen.somtoday.nl/oauth2/authorize",
                                        params=payload,
                                        follow_redirects=False)
            cookies_saved = response.cookies
            parsed = urlparse(response.headers.get("location"))
            auth_token = parse_qs(parsed.query).get("auth")[0]

            post_headers = {
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://inloggen.somtoday.nl"
            }
            firstpos = await client.post("https://inloggen.somtoday.nl/", data={
                "loginLink": "x",
                "usernameFieldPanel:usernameFieldPanel_body:usernameField": name,
                "passwordFieldPanel:passwordFieldPanel_body:passwordField": password
            }, params={"-1.-panel-signInForm": "",
                       "auth": auth_token, "1-1.-passwordForm": ""},
                                         headers=post_headers,
                                         follow_redirects=False,
                                         cookies=cookies_saved)

            cookies_saved = firstpos.cookies
            location2 = firstpos.headers.get('location')
            code_as_return: str = None
            if location2.startswith("somtodayleerling:"):
                parsed_url = urlparse(location2)
                code_as_return: str = parse_qs(parsed_url.query).get("code")[0]
            else:
                thirdpost = await client.post(
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
                    allow_redirects=False
                )
                location3 = thirdpost.headers.get("location")
                if location3.startswith("somtodayleerling:"):
                    parsed_url = urlparse(location3)
                    code_as_return: str = parse_qs(parsed_url.query).get("code")[0]
                else:
                    self.__failed_time += 1
                    return await self.get_student(name, password)
            last_response_payload = {
                "grant_type": "authorization_code",
                "scope": "openid",
                "client_id": "D50E0C06-32D1-4B41-A137-A9A850C892C2",
                "tenant_uuid": self.school_uuid,
                "session": "no_session",
                "code": code_as_return,
                "code_verifier": token
            }
            last_response_headers = {
                "content-type": "application/x-www-form-urlencoded"
            }
            final_response = await client.post("https://inloggen.somtoday.nl/oauth2/token",
                                               data=last_response_payload,
                                               headers=last_response_headers)
            if final_response.status_code == 200:
                to_dict = final_response.json()
                new_student_created = Student(name=name,
                                              password=password,
                                              uuid=self.school_uuid,
                                              literal_school=self.school_name,
                                              auth_code=auth_token,
                                              access=to_dict["access_token"],
                                              refresh=to_dict["refresh_token"])
                await new_student_created.load_more_data()
                return new_student_created

            else:
                raise ValueError(f"request failed: code {final_response.status_code}")


async def find_school(school_name: str) -> School:
    """gets & returns a School object, alternative to School.from_school_name(name)
    Args:
        school_name (str): name of the school

    Raises:
        ValueError: School is not registered by somtoday or school_name invalid

    Returns:
        School: The School model  representation
    """
    async with httpx.AsyncClient() as client:
        schoolresponse = await client.get("https://servers.somtoday.nl/organisaties.json")
        response_as_dict = schoolresponse.json()
        final_result = tuple(filter(
            lambda school_dict: school_dict["naam"].lower() == school_name.lower(),
            response_as_dict[0]["instellingen"]))
        if final_result:
            return School(school_name, final_result[0]["uuid"])
        else:
            raise ValueError(f"{school_name} does not exist")
