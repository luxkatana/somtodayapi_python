'''
Module that provide non-asynchronous functions for using the somtoday API

'''
import base64
import re
from typing import Any, Union, Generator
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from hashlib import sha256
from random import choice
from string import ascii_lowercase, digits
from urllib.parse import urlparse, parse_qs
import httpx


class PasFoto:
    def __init__(self, b64url: str):
        self.base64url: bytes = b64url[21::].encode()

    def save(self, save_to: Path) -> Union[bool, Exception]:
        """save the PasFoto as file

        Args:
            save_to (Path): file where it should save the PasFoto

        Returns:
            bool: returns True if everything was gone successfully
        """
        try:
            with open(save_to, "wb") as f:
                f.write(base64.decodebytes(self.base64url))
                return True
        except Exception as e:
            raise e


@dataclass
class Cijfer:
    vak: str
    datum: datetime
    leerjaar: int
    resultaat: str

    def __eq__(self, other):
        if isinstance(other, Cijfer):
            return self.resultaat == other.resultaat
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Cijfer):
            return self.resultaat < other.resultaat
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Cijfer):
            return self.resultaat <= other.resultaat
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Cijfer):
            return self.resultaat > other.resultaat
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Cijfer):
            return self.resultaat >= other.resultaat
        return NotImplemented


class Subject:
    '''
    Subject:
    a model what represents a single school subject/hour from timetable
    THIS IS NOT MEANT TO BE CREATED BY THE USER
    '''
    subject_name: str
    begin_time: datetime
    end_time: datetime
    subject_short: str
    begin_hour: int
    end_hour: int
    location: str
    teacher_short: str

    def __init__(self, **kwargs: dict[str, Any]):
        self.subject_name: str = kwargs.get("subject")
        self.begin_time: datetime = kwargs.get("begindt")
        self.end_time: datetime = kwargs.get("enddt")
        self.subject_short: str = kwargs.get("subject_short")
        self.begin_hour: int = kwargs.get("beginhour")
        self.end_hour: int = kwargs.get("endhour")
        self.location: str = kwargs.get("location")
        self.teacher_short: str = kwargs.get("teacher_shortcut")


class Student:
    '''
    Student:
        Model that represents a Student
        THIS IS NOT MEANT TO BE CREATED BY THE USER
    '''

    def __init__(self, **kwargs):
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
        self.load_more_data()

    def __eq__(self, __value: Any) -> bool:
        if isinstance(__value, Student):
            return self.name == __value.name and self.school_name == __value.school_name
        return NotImplemented
    def yield_fetch_cijfers(self, lower_bound_range: int, upper_bound_range: int) -> Generator[Cijfer, Cijfer, Cijfer]:
        """yields the cijfers by calling self.fetch_cijfers() and yielding it results
        Args:
            lower_bound_range (int):  minimum to return (must be greater than 0 and fewer than 100)
            upper_bound_range (int):  maximum to return (must be fewer than 100)

        Yields:
            cijfer: Cijfer object
        """        
        
        cijfers = self.fetch_cijfers(lower_bound_range, upper_bound_range)
        for cijfer in cijfers:

            yield cijfer


    def fetch_cijfers(self, lower_bound_range: int, upper_bound_range: int) -> list[Cijfer]:
        """fetches the cijfers and saves it to self.cijfers

        Args:
            lower_bound_range (int): minimum to return (must be greater than 0 and fewer than 100)
            upper_bound_range (int): maximum to return (must be fewer than 100)
        Raises:
            ValueError: lower_bound_range or upper_boung_range is negative or more than 100
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
        response = httpx.get(f"{self.endpoint}/rest/v1/resultaten/huidigVoorLeerling/{self.indentifier}",
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
                cijfer_Object: Cijfer = Cijfer(vak=vak, datum=tijd_nagekeken, leerjaar=leerjaar, resultaat=resultaat)
                self.cijfers.append(cijfer_Object)
            self.dump_cache = to_dict
            return self.cijfers
        else:
            raise ExceptionGroup("error", [
                [
                    f"response returned status code {response.status_code} from {self.endpoint}/rest/v1/resultaten/huidigVoorLeerling/{self.indentifier}"
                ]
            ])
    
    def yield_fetch_schedule(self,
                             begindt: datetime,
                             enddt: datetime,
                             group_by_day: bool = False):
        """Yielding each ``Subject`` object 

        Args:
            begindt (datetime): starting date to fetch
            enddt (datetime): ending date to fetch
            group_by_day (bool, optional): to group it by day. Defaults to False.
        """        
        schedule = self.fetch_schedule(begindt, enddt, group_by_day)
        for subject in schedule:
            yield subject

    def fetch_schedule(self,
                       begindt: datetime,
                       enddt: datetime,
                       group_by_day: bool = False) -> list[Union[Subject, list[Subject]]]:
        """description: fetches the timetable and saves it to self.school_subjects
        Args:
            begindt (datetime): starting date to fetch
            enddt (datetime):   ending date to fetch
            group_by_day (bool, optional): to group it by day. Defaults to False.

        Returns:
            list[Subject]  | list[list[Subject]]:  list what contains Subjects or a grouped Subjects
        """
        params_payload = {
            "begindatum": f"{begindt.year}-{begindt.month}-{begindt.day}",
            "einddatum": f"{enddt.year}-{enddt.month}-{enddt.day}",
            "additional": ["vak", "docentAfkortingen"],
            "sort": "asc-beginDatumTijd"
        }
        response = httpx.get(f"{self.endpoint}/rest/v1/afspraken",
                          headers={"Accept": "application/json",
                                   "Authorization": f"Bearer {self.access_token}"},
                          params=params_payload,
                          timeout=30) 
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
                    begin_time.strftime("%Y-%m-%d"))
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

    def __repr__(self):
        return f"{self.full_name}, {self.school_name}"

    def __str__(self):
        return self.__repr__()

    def load_more_data(self) -> bool:
        """description: generates data(not meant to be called)

        Returns:
            bool: if it fetched and loaded data with success.
        """
        if hasattr(self, "full_name"):
            return False
        else:
            name_response = httpx.get(f"{self.endpoint}/rest/v1/leerlingen",
                              headers={
                                  "Authorization":
                                      f"Bearer {self.access_token}",
                                  "Accept": "application/json"},
                              params={"additional": ["pasfoto", "leerlingen"]},

                              timeout=30) 
            to_dict = name_response.json()["items"][0]
            self.pasfoto = PasFoto(to_dict["additionalObjects"]["pasfoto"]["datauri"])
            self.full_name = to_dict.get(
                "roepnaam") + " " + to_dict.get("achternaam")
            self.indentifier = to_dict.get("links")[0]["id"]
            self.email = to_dict.get("email")
            self.leerlingnummer = to_dict.get("leerlingnummer")
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

    def __init__(self, school_name: str, uuid: str):
        self.school_name = school_name
        self.school_uuid = uuid

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
        school_response = httpx.get("https://servers.somtoday.nl/organisaties.json",
                          timeout=30)
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
    
    @staticmethod
    def _generate_random_str(length: int) -> str:
        return "".join([choice(ascii_lowercase + digits) for _ in range(length)])

    
    @staticmethod
    def parse_query_url(key: str, url: str) -> Union[str, None]:
        return parse_qs(urlparse(url).query)[key]
    def get_student(self, name: str, password: str) -> Student:
        """description: Gets the student by name and password(without SSO)
        Args:
            name (str):  The student's name - The login name you use to login at inloggen.somtoday.nl
            password (str):  The student's password

        Raises:
            ValueError: Credentials are incorrect.
            httpx.exceptions.RequestException: Error at  last https request. Rarely happens.

        Returns:
            Student: The student self.
        """

        with httpx.Client(follow_redirects=False) as session:
            codeVerifier: str = self._generate_random_str(128)
            codeChallenge = base64.b64encode(sha256(codeVerifier.encode()).digest()).decode()
            codeChallenge = re.sub(r"\+", "-", codeChallenge)
            codeChallenge = re.sub(r"\/", "_", codeChallenge)
            codeChallenge = re.sub(r"=+$", "", codeChallenge)

            response = session.get(
                "https://inloggen.somtoday.nl/oauth2/authorize",
                params={
                    "redirect_uri": "somtodayleerling://oauth/callback",
                    "client_id": "D50E0C06-32D1-4B41-A137-A9A850C892C2",
                    "state": self._generate_random_str(8),
                    "response_type": "code",
                    "scope": "openid",
                    "tenant_uuid": self.school_uuid,
                    "session": "no_session",
                    "code_challenge": codeChallenge,  # TODO
                    "code_challenge_method": "S256",
                },
            )
            session.get(response.headers['location'])
            authorization_code = self.parse_query_url("auth", response.headers['location'])
            response = session.post(
                "https://inloggen.somtoday.nl/?0-1.-panel-signInForm",
                params={"auth": authorization_code},
                headers={"origin": "https://inloggen.somtoday.nl"},
            )
            if 'auth=' in response.headers['Location']: # username + password directly 
                    data = {
                        "loginLink": "x",
                        "usernameFieldPanel:usernameFieldPanel_body:usernameField": name,
                        "passwordFieldPanel:passwordFieldPanel_body:passwordField": password
                    }
                    response = session.post(
                        "https://inloggen.somtoday.nl/?0-1.-panel-signInForm",
                        data=data,
                        headers={"origin": "https://inloggen.somtoday.nl"},
                        params={"auth": authorization_code},
                    )

            else: # first username, then password 
                data = {
                    'loginLink': 'x',
                    "passwordFieldPanel:passwordFieldPanel_body:passwordField": password
                }
                response = httpx.post(
                    "https://inloggen.somtoday.nl/login?2-1.-passwordForm",
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Origin": "https://inloggen.somtoday.nl",
                    },
                    data=data,
                )
            callback_oauth: str = response.headers['Location']
            if callback_oauth.startswith("somtodayleerling://"):
                params = {
                    "grant_type": "authorization_code",
                    "session": "no_session",
                    "scope": "openid",
                    "client_id": "D50E0C06-32D1-4B41-A137-A9A850C892C2",
                    "tenant_uuid": self.school_uuid,
                    "code": self.parse_query_url('code', callback_oauth),
                    "code_verifier": codeVerifier,
                }
                response = session.post(
                    "https://inloggen.somtoday.nl/oauth2/token",
                    params=params,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response_json = response.json()
                return Student(name=name,
                password=password,
                uuid=self.school_uuid,
                literal_school=self.school_name,
                auth_code=authorization_code,
                access=response_json["access_token"],
                refresh=response_json["refresh_token"])
            else:
                raise Exception('todo')
                
            
        # if last_response_final_response.status_code == 200:
        #     to_dict = last_response_final_response.json()
        #     return Student(name=name,
        #                    password=password,
        #                    uuid=self.school_uuid,
        #                    literal_school=self.school_name,
        #                    auth_code=auth_token,
        #                    access=to_dict["access_token"],
        #                    refresh=to_dict["refresh_token"])
        # else:
        #     raise httpx.exceptions.RequestException(
        #         f"request failed. request code {last_response_final_response.status_code}")


def find_school(school_name: str) -> School:
    """description: Function that returns a school by name

    Args:
        school_name (str): The school's name

    Raises:
        ValueError: The school_name parameter is incorrect.

    Returns:
        School: A school object representing the school name + school uuid (tenant_uuid)
    """
    schoolresponse = httpx.get("https://servers.somtoday.nl/organisaties.json", timeout=30) 
    response_as_dict = schoolresponse.json()
    final_result = tuple(filter(lambda school_dict: school_dict["naam"].lower(
    ) == school_name.lower(), response_as_dict[0]["instellingen"]))

    if final_result:
        return School(school_name, final_result[0]["uuid"])
    else:
        raise ValueError(f"{school_name} does not exist")
