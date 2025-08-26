"""
Module that provide non-asynchronous functions for using the somtoday API

"""

import base64
from io import BytesIO
import re
import requests
import pytz
from typing import Any, Union, Generator
from datetime import datetime
from dataclasses import dataclass
from hashlib import sha256
from random import choice
from string import ascii_lowercase, digits
from urllib.parse import urlparse, parse_qs

CET = pytz.timezone("Europe/Amsterdam")


class PasFoto:
    def __init__(self, pasfoto_bytes: bytes):
        self.pasfoto_bytes = pasfoto_bytes

    def save(self, fp: BytesIO) -> bool:
        """save/write the PasFoto to a BytesIO Stream (will not close the stream)

        Args:
            fp (BytesIO): A stream/file/file pointer to write the PasFoto to

        Raises:
            Exception: If something went wrong while writing
        """
        try:
            fp.write(self.pasfoto_bytes)
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
    """
    Subject:
    a model what represents a single school subject/hour from timetable
    THIS IS NOT MEANT TO BE CREATED BY THE USER
    """

    subject_name: str
    begin_time: datetime
    end_time: datetime
    subject_short: str
    begin_hour: int
    end_hour: int
    location: str
    teacher: str

    def __init__(self, **kwargs: dict[str, Any]):
        self.subject_name: str = kwargs.get("subject")
        self.begin_time: datetime = kwargs.get("begindt")
        self.end_time: datetime = kwargs.get("enddt")
        self.subject_short: str = kwargs.get("subject_short")
        self.begin_hour: int = kwargs.get("beginhour")
        self.end_hour: int = kwargs.get("endhour")
        self.location: str = kwargs.get("location")
        self.teacher: str = kwargs.get("teacher_shortcut")

    def __hash__(self) -> int:
        return (
            hash(self.subject_name)
            + hash(self.begin_time)
            + hash(self.end_time)
            + hash(self.subject_short)
            + hash(self.begin_hour)
            + hash(self.end_hour)
            + hash(self.location)
            + hash(self.teacher)
        )


class Student:
    """
    Student:
        Model that represents a Student
    """

    @classmethod
    def from_access_token(
        cls,
        access_token: str,
        refresh_token: str,
        school: Union["School", None] = None,
    ) -> "Student":
        """
        Creates a Student object with the given access and refresh token.

        Args:
            access_token: the access token
            refresh_token: The refresh token
            school_name (optional): The school object.
            **NOTE: If the ``school`` is None, then Student.school_name & Student.school_uuid will be undefined**


        Returns:
            a Student object - without Student.password
        Raises:
            ValueError: if the access_token is invalid.

        """

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        gebruikersnaam_response = requests.get(
            "https://api.somtoday.nl/rest/v1/account/", headers=headers
        )
        if gebruikersnaam_response.status_code == 401:
            return ValueError("Invalid access_token (api returned with 401)")

        gebruikersnaam = gebruikersnaam_response.json()["items"][0]["gebruikersnaam"]

        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            gebruikersnaam=gebruikersnaam,
            school_obj=school,
        )

    def __del__(self):
        self.api_adapter.close()

    def __init__(
        self,
        access_token: Union[str, None] = None,
        refresh_token: Union[str, None] = None,
        **kwargs,
    ):
        if access_token is None and refresh_token is None:  # defined by get_student
            self.name: str = kwargs.get("name")
            self.password: str = kwargs.get("password")
            self.school_uuid: str = kwargs.get("uuid")
            self.school_name: str = kwargs.get("literal_school")
        else:
            self.name = kwargs.get("gebruikersnaam")
            school_obj: "School" = kwargs.get("school_obj", None)
            if school_obj is not None:
                self.school_uuid = school_obj.school_uuid
                self.school_name = school_obj.school_name

        self.endpoint = "https://api.somtoday.nl"
        self.access_token: str = kwargs.get("access", access_token)
        self.refresh_token: str = kwargs.get("refresh", refresh_token)
        self.school_subjects: list[Union[Subject, list[Subject]]] = []
        self.api_adapter = requests.Session()
        self.api_adapter.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            }
        )
        self.email: str
        self.full_name: str
        self.gender: str
        self.cijfers: list[Cijfer]
        self.leerlingnummer: int
        self.identifier: int
        self.birth_datetime: datetime
        self.pasfoto: PasFoto
        self.dump_cache: dict[str]
        self.load_more_data()

    def __eq__(self, __value: Any) -> bool:
        if isinstance(__value, Student):
            return self.name == __value.name and self.school_name == __value.school_name
        return False

    def yield_fetch_cijfers(
        self, lower_bound_range: int, upper_bound_range: int
    ) -> Generator[Cijfer, Cijfer, Cijfer]:
        """yields the cijfers by calling Student.fetch_cijfers() and yielding it's results
        You may only fetch max grades so (please also take a look at Student.fetch_cijfers's docstring)
        (upper_boung_range - lower_bound_range) < 100 is valid
        Args:
            lower_bound_range (int):  minimum of the pagination
            upper_bound_range (int):  maximum of the pagination

        Yields:
            cijfer: Cijfer object
        Raises:
            ValueError: You may only fetch 99 grades max
        """
        if (upper_bound_range - lower_bound_range) > 99:
            raise ValueError("You may only fetch 99 grades max")

        cijfers = self.fetch_cijfers(lower_bound_range, upper_bound_range)
        for cijfer in cijfers:
            yield cijfer

    def fetch_cijfers(
        self, lower_bound_range: int, upper_bound_range: int
    ) -> list[Cijfer]:
        """Fetches the grades. SOMToday uses a pagination system,
        therefore you can only fetch max 99 grades at a time.
        NOTE: SOMToday sometimes has the tendency to also provide school grades from previous school years + some rapportcolumns
        The Cijfer.resultaat may be ``NIET_GEGEVEN`` if the resultaat couldn't be fetched from the grades api call.

        NOTE: SOMToday sometimes has the tendency to also provide school grades from previous school years + some rapportcolumns
        The Cijfer.resultaat may be ``NIET_GEGEVEN`` if the resultaat couldn't be fetched from the grades api call of SOMToday.

        Args:
            lower_bound_range (int): Minimum of the pagination
            upper_bound_range (int): Maximum of the pagination
        Raises:
            ValueError: (upper_bound_range - lower_bound_range) is 100 or more
            ExceptionGroup: status code is unexpected

        Returns:
            list[Cijfer]: list of Cijfers
        """
        if (upper_bound_range - lower_bound_range) > 99:
            raise ValueError("You may only fetch 99 grades max")
        headers = {
            "Range": f"items={lower_bound_range}-{upper_bound_range}",
        }
        response = self.api_adapter.get(
            f"{self.endpoint}/rest/v1/resultaten/huidigVoorLeerling/{self.identifier}",
            headers=headers,
        )
        if response.status_code >= 200 and response.status_code < 300:
            to_dict = response.json()
            items: list[dict] = to_dict["items"]
            self.cijfers = []
            for item in items:
                tijd_nagekeken = datetime.fromisoformat(item["datumInvoer"]).replace(
                    tzinfo=CET
                )
                resultaat = item.get("resultaat", "NIET_GEGEVEN")
                leerjaar = item["leerjaar"]
                vak = item["vak"]["naam"]
                cijfer_Object: Cijfer = Cijfer(
                    vak=vak,
                    datum=tijd_nagekeken,
                    leerjaar=leerjaar,
                    resultaat=resultaat,
                )
                self.cijfers.append(cijfer_Object)
            self.dump_cache = to_dict
            return self.cijfers
        else:
            raise Exception(
                f"response returned status code {response.status_code} from {self.endpoint}/rest/v1/resultaten/huidigVoorLeerling/{self.identifier}"
            )

    def yield_fetch_schedule(
        self, begindt: datetime, enddt: datetime, group_by_day: bool = False
    ):
        """Yielding each ``Subject`` object

        Args:
            begindt (datetime): starting date to fetch
            enddt (datetime): ending date to fetch
            group_by_day (bool, optional): to group it by day. Defaults to False.
        """
        schedule = self.fetch_schedule(begindt, enddt, group_by_day)
        for subject in schedule:
            yield subject

    def fetch_schedule(
        self, begindt: datetime, enddt: datetime, group_by_day: bool = False
    ) -> list[Union[Subject, list[Subject]]]:
        """description: fetches the timetable and saves it to self.school_subjects
        Args:
            begindt (datetime): starting date to fetch
            enddt (datetime):   ending date to fetch
            group_by_day (bool, optional): to group it by day. Defaults to False.

        Returns:
            list[Subject]  | list[list[Subject]]:  list what contains Subjects or a grouped Subjects
        """
        params_payload = {
            "begindatum": begindt.strftime("%Y-%m-%d"),
            "einddatum": enddt.strftime("%Y-%m-%d"),
            "additional": ["vak", "docentAfkortingen"],
            "sort": "asc-beginDatumTijd",
        }
        response = self.api_adapter.get(
            f"{self.endpoint}/rest/v1/afspraken",
            params=params_payload,
            timeout=30,
        )
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
            docent_afkorting: str = item.get("additionalObjects").get(
                "docentAfkortingen"
            )
            begin_time: datetime = datetime.fromisoformat(
                item.get("beginDatumTijd")
            ).replace(tzinfo=CET)
            end_time: datetime = datetime.fromisoformat(
                item.get("eindDatumTijd")
            ).replace(tzinfo=CET)
            target_object = Subject(
                subject=subject_name,
                begindt=begin_time,
                enddt=end_time,
                subject_short=afkorting,
                beginhour=begin_lesuur,
                endhour=eind_lesuur,
                location=locatie,
                teacher=docent_afkorting,
            )
            if group_by_day:
                begin_time_formatted = begin_time.strftime("%Y-%m-%d")
                if begin_time_formatted in groups:
                    # group = groups.get(begin_time.strftime("%Y-%m-%d"))
                    groups[begin_time_formatted].append(target_object)
                    # group.append(target_object)
                else:
                    # new_group = {begin_time.strftime("%Y-%m-%d"): [target_object]}
                    groups[begin_time_formatted] = [target_object]
                    # groups.update(new_group)
            else:
                self.school_subjects.append(target_object)
        if group_by_day:
            self.school_subjects = [groups[x] for x in groups]
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
            name_response = self.api_adapter.get(
                f"{self.endpoint}/rest/v1/leerlingen",
                timeout=30,
            )
            to_dict = name_response.json()["items"][0]

            self.pasfoto = PasFoto(
                self.api_adapter.get(to_dict["pasfotoUrl"]).text.encode()
            )
            self.full_name = to_dict.get("roepnaam") + " " + to_dict.get("achternaam")
            self.identifier = to_dict.get("links")[0]["id"]
            self.email = to_dict.get("email")
            self.leerlingnummer = to_dict.get("leerlingnummer")
            self.gender = "Male" if to_dict.get("geslacht") == "Man" else "Female"
            year, month, day = to_dict.get("geboortedatum").split("-")
            self.birth_datetime = datetime(int(year), int(month), int(day), tzinfo=CET)
        return True

    @property
    def school_object(self) -> "School":
        """description: The school object if Student.school_name & Student.school_uuid is defined (School)

        Returns:
            School: The School where the student has been fetched.
        """
        return School(self.school_name, self.school_uuid)


class School:
    """
    Model that represents a school.
    NOT MEANT TO BE CREATED BY THE USER
    """

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
            School: School object
        """
        school_response = requests.get(
            "https://raw.githubusercontent.com/NONtoday/organisaties.json/refs/heads/main/organisaties.json"
        )
        as_dict = school_response.json()
        instellingen = as_dict[0]["instellingen"]
        exists = tuple(filter(lambda school_: school_["uuid"] == uuid, instellingen))
        if exists:
            return School(exists[0]["naam"], uuid)
        else:
            raise ValueError(f"Invalid uuid")

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
        """description: Gets the student by name and password (not for accounts that has SSO authentication)
        Args:
            name (str):  The student's name - The login name you use to login at inloggen.somtoday.nl
            password (str):  The student's password

        Raises:
            Exception: Credentials are incorrect. Or account needs SSO authentication
        Returns:
            Student: The student object.
        """

        with requests.Session() as session:
            codeVerifier: str = self._generate_random_str(128)
            codeChallenge = base64.b64encode(
                sha256(codeVerifier.encode()).digest()
            ).decode()
            codeChallenge = re.sub(r"\+", "-", codeChallenge)
            codeChallenge = re.sub(r"\/", "_", codeChallenge)
            codeChallenge = re.sub(r"=+$", "", codeChallenge)

            response = session.get(
                "https://inloggen.somtoday.nl/oauth2/authorize",
                params={
                    "redirect_uri": "somtoday://nl.topicus.somtoday.leerling/oauth/callback",
                    "client_id": "somtoday-leerling-native",
                    "state": self._generate_random_str(8),
                    "response_type": "code",
                    "scope": "openid",
                    "tenant_uuid": self.school_uuid,
                    "session": "no_session",
                    "code_challenge": codeChallenge,
                    "code_challenge_method": "S256",
                },
                allow_redirects=False,
            )
            session.send(response.next, allow_redirects=False)
            authorization_code = self.parse_query_url("auth", response.next.url)[0]
            response = session.post(
                "https://inloggen.somtoday.nl/?0-1.-panel-signInForm",
                params={"auth": authorization_code},
                headers={"origin": "https://inloggen.somtoday.nl"},
                allow_redirects=False,
            )
            if "auth=" in response.next.url:  # username + password directly
                data = {
                    "loginLink": "x",
                    "usernameFieldPanel:usernameFieldPanel_body:usernameField": name,
                    "passwordFieldPanel:passwordFieldPanel_body:passwordField": password,
                }
                response = session.post(
                    "https://inloggen.somtoday.nl/?0-1.-panel-signInForm",
                    data=data,
                    headers={
                        "origin": "https://inloggen.somtoday.nl",
                    },
                    params={
                        "auth": authorization_code,
                    },
                    allow_redirects=False,
                )

            else:  # first username, then password
                data = {
                    "loginLink": "x",
                    "passwordFieldPanel:passwordFieldPanel_body:passwordField": password,
                }
                response = session.post(
                    "https://inloggen.somtoday.nl/login?2-1.-passwordForm",
                    headers={
                        "origin": "https://inloggen.somtoday.nl",
                    },
                    data=data,
                    params={"auth": authorization_code},
                    allow_redirects=False,
                )
            # callback_oauth: str = response.headers["Location"]
            callback_oauth = response.next.url
            if callback_oauth.startswith("somtoday://"):
                params = {
                    "grant_type": "authorization_code",
                    "session": "no_session",
                    "scope": "openid",
                    "client_id": "somtoday-leerling-native",
                    "tenant_uuid": self.school_uuid,
                    "code": self.parse_query_url("code", callback_oauth),
                    "code_verifier": codeVerifier,
                }
                response = session.post(
                    "https://inloggen.somtoday.nl/oauth2/token",
                    params=params,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response_json = response.json()
                return Student(
                    name=name,
                    password=password,
                    uuid=self.school_uuid,
                    literal_school=self.school_name,
                    access=response_json["access_token"],
                    refresh=response_json["refresh_token"],
                )
            elif callback_oauth.startswith("https://inloggen.somtoday.nl"):
                raise Exception(
                    "Credentials are incorrect (after entering credentials, SOMToday redirected to https://inloggen.somtoday.nl)"
                )
            else:
                return Exception(
                    "Account has SSO authentication, please have a look at https://github.com/luxkatana/somtodayapi_python/issues/5#issuecomment-3104658720"
                )


def find_school(school_name: str) -> School:
    """description: Function that returns a school by name

    Args:
        school_name (str): The school's name

    Raises:
        ValueError: The school_name parameter is incorrect.

    Returns:
        School: A school object representing the school name + school uuid (tenant_uuid)
    """
    schoolresponse = requests.get(
        "https://raw.githubusercontent.com/NONtoday/organisaties.json/refs/heads/main/organisaties.json",
        timeout=30,
    )
    response_as_dict = schoolresponse.json()
    final_result = tuple(
        filter(
            lambda school_dict: school_dict["naam"].lower() == school_name.lower(),
            response_as_dict[0]["instellingen"],
        )
    )

    if final_result:
        return School(school_name, final_result[0]["uuid"])
    else:
        raise ValueError(f"{school_name} does not exist")
