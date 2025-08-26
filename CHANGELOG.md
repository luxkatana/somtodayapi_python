# Changes in 1.2.1
- setup.py has been removed
- using pyproject.toml
- There is not an examples folder
- PasFoto.save takes an BytesIO object instead of a Path
- Student.from_access_token's functionality has been extended
- Removal of Student.auth_code (is nowhere used anyways)
- Updated docstrings
- Better explanation for Student.fetch_cijfers 
- If the resultaat of a cijfer is unknown, then it'll be ``NIET_GEGEVEN`` instead of ``0``
- Student.indentifier -> Student.identifier (Misspelling)
- Removed additional params for Student.fetch_cijfers method 
- Add of http sessions when interacting with Student data fetching
- Subject.teacher_short -> Subject.teacher
- True checking if credentials are wrong
- True checking if account needs SSO authentication

# Changes in 1.2.2 [CRUCIAL]
- Could not make a proper Student object which has been fixed now
- Using another way of obtaining the Student.pasfoto

