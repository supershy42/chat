import requests

USER_SERVICE_URL = "http://127.0.0.1/api/user/"

def is_valid_user(user_id):
    try:
        response = requests.get(f"{USER_SERVICE_URL}{user_id}/")
        if response.status_code == 200:
            return True
        return False
    except requests.RequestException as e:
        return False