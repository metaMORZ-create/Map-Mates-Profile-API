import requests
import random

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

def add_location(user_id: int, latitude: int, longitude: int):
    url_add_location = "https://map-mates-profile-api-production.up.railway.app/locations/add_location"
    data_add_location = {"user_id": user_id, "latitude": latitude, "longitude": longitude}
    response = requests.post(url_add_location, json=data_add_location)

    return response

def get_last_location(user_id: int):
    url_add_location = f"https://map-mates-profile-api-production.up.railway.app/locations/last_location/{user_id}"
    response = requests.get(url_add_location)

    return response



def full_test():
    response_create = create_user(username="Tester", email="test@test.test", password="test123")
    response_login = login_user(username="Tester", password="test123")
    response_delete = delete_user(username="Tester")
    response_add_location = add_location(user_id=1, latitude=random.randrange(10, 60), longitude=random.randrange(10, 60))
    response_get_location = get_last_location(user_id=1)

    print(f"Create User Status: {response_create.status_code} \nMessage: {response_create.text}")
    print(f"Login User Status: {response_login.status_code} \nMessage: {response_login.text}")
    print(f"Delete User Status: {response_delete.status_code} \nMessage: {response_delete.text}")
    print(f"Add Location Status: {response_add_location.status_code} \nMessage: {response_add_location.text}")
    print(f"Got Location Status: {response_get_location.status_code} \nMessage: {response_get_location.text}")



if __name__ == "__main__":
   # response = delete_user("Stine")
   # print(f"Status: {response.status_code} \nMessage: {response.text}")
   full_test()
   #response_get_location = get_last_location(user_id=1) 
   #print(f"Status: {response_get_location.status_code} \nMessage: {response_get_location.text}")