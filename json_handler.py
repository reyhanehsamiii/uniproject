# models/json_handler.py
import json
import os


class JSONHandler:
    @staticmethod
    def read_json(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file) 
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def write_json(file_path, data):
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
