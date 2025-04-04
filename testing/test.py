import requests

def create_user(username: str, email: str, password: str):
    url_register = "https://map-mates-profile-api-production.up.railway.app/users/register"
    data_create_user = {"username": username, "email": email, "password": password}
    response = requests.post(url_register, json=data_create_user)

    return response

def login_user(username: str, password: str):
    url_login = "https://map-mates-profile-api-production.up.railway.app/users/login"
    data_login_user = {"username": username, "password": password}
    response = requests.post(url_login, json=data_login_user)

    return response

def delete_user(username: str):
    url_delete = f"https://map-mates-profile-api-production.up.railway.app/users/delete/{username}"
    response = requests.delete(url_delete)

    return response

def full_test():
    response_create = create_user(username="Tester", email="test@test.test", password="test123")
    response_login = login_user(username="Tester", password="test123")
    response_delete = delete_user(username="Tester")

    print(f"Create User Status: {response_create.status_code} \nMessage: {response_create.text}")
    print(f"Login User Status: {response_login.status_code} \nMessage: {response_login.text}")
    print(f"Delete User Status: {response_delete.status_code} \nMessage: {response_delete.text}")

if __name__ == "__main__":
   # response = delete_user("Stine")
   # print(f"Status: {response.status_code} \nMessage: {response.text}")
   full_test()