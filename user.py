# models/user.py
class User:
    def __init__(self, user_id, username, password, name="", role="student"):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.name = name
        self.role = role

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "password": self.password,
            "name": self.name,
            "role": self.role
        }

    @staticmethod
    def from_dict(data):
        return User(
            data.get("user_id"),
            data.get("username"),
            data.get("password"),
            data.get("name", ""),
            data.get("role", "student")
        )


class Student(User):
    def __init__(self, user_id, username, password, name=""):
        super().__init__(user_id, username, password, name, role="student")


class Administrator(User):
    def __init__(self, user_id, username, password, name=""):
        super().__init__(user_id, username, password, name, role="admin")
