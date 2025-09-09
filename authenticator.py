# utils/authenticator.py
import uuid
from models.user import User, Student, Administrator
from models.json_handler import JSONHandler

class Authenticator:
    @staticmethod
    def login(username, password):
        users = JSONHandler.read_json('data/users.json')
        for user in users:
            if user['username'] == username and user['password'] == password:
                return User.from_dict(user)
        return None
    
    @staticmethod
    def register(username, password, name, role="student"):
        users = JSONHandler.read_json('data/users.json')
        
        # Check if username already exists
        if any(user['username'] == username for user in users):
            return False
        
        # Create new user
        user_id = str(uuid.uuid4())
        
        if role == "admin":
            new_user = Administrator(user_id, username, password, name)
        else:
            new_user = Student(user_id, username, password, name)
        
        users.append(new_user.to_dict())
        JSONHandler.write_json('data/users.json', users)
        return True
