# models/registration.py
class Registration:
    def __init__(self, reg_id, user_id, course_id, registration_date):
        self.reg_id = reg_id
        self.user_id = user_id
        self.course_id = course_id
        self.registration_date = registration_date
    
    def to_dict(self):
        return {
            "reg_id": self.reg_id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "registration_date": self.registration_date
        }
    
    @staticmethod
    def from_dict(data):
        return Registration(
            data.get("reg_id"),
            data.get("user_id"),
            data.get("course_id"),
            data.get("registration_date")
        )
