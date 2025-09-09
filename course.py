# models/course.py
class Course:
    def __init__(
        self, course_id, title, description, schedule, capacity, prerequisites=None
    ):
        self.course_id = course_id
        self.title = title
        self.description = description
        self.schedule = schedule  # List of {"day": "Monday", "start_time": "10:00", "end_time": "12:00"}
        self.capacity = capacity
        self.prerequisites = prerequisites or []

    def to_dict(self):
        return {
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "schedule": self.schedule,
            "capacity": self.capacity,
            "prerequisites": self.prerequisites,
        }

    @staticmethod
    def from_dict(data):
        return Course(
            data.get("course_id"),
            data.get("title"),
            data.get("description"),
            data.get("schedule"),
            data.get("capacity"),
            data.get("prerequisites", []),
        )
 