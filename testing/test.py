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

def search_user(search: str, user_id: int):
    url_search_user = f"https://map-mates-profile-api-production.up.railway.app/socials/search?query={search}&self_id={user_id}"
    response = requests.get(url_search_user)

    return response

def send_request(sender_id: int, receiver_id: int):
    url_send_request = f"https://map-mates-profile-api-production.up.railway.app/socials/send_request"
    data_send_request = {"sender_id": sender_id, "receiver_id": receiver_id}
    response = requests.post(url_send_request, json=data_send_request)

    return response

def accept_request(self_user_id: int, sender_user_id: int):
    url_accept_request = f"https://map-mates-profile-api-production.up.railway.app/socials/accept_request"
    data_accept_request = {"self_user_id": self_user_id, "sender_user_id": sender_user_id}
    response = requests.post(url_accept_request, json=data_accept_request)

    return response

def deny_request(self_user_id: int, sender_user_id: int):
    url_deny_request = f"https://map-mates-profile-api-production.up.railway.app/socials/deny_request"
    data_deny_request = {"self_user_id": self_user_id, "sender_user_id": sender_user_id}
    response = requests.post(url_deny_request, json=data_deny_request)

    return response

def get_outgoing_requests(self_id: int):
    friends = [1, 12, 4, 5, 8]
    for friend in friends:
        response_send = send_request(sender_id=3, receiver_id=friend)
        if response_send.status_code != 200:
            print(f"!!!!! FEHLER BEIM SENDEN DER FRIENDREQUESTS: {response_send.text}")
    url_outgoing_requests = f"https://map-mates-profile-api-production.up.railway.app/socials/outgoing_requests/{self_id}"
    response = requests.get(url_outgoing_requests)

    for friend in friends:
        response_denied = deny_request(self_user_id=3, sender_user_id=friend)
        if response_denied.status_code != 200:
            print(f"!!!!! FEHLER BEIM LÖSCHEN DER FRIEND REQUESTS: {response_denied.text}")


    return response

def get_incoming_requests(self_id: int):
    url_incoming_requests = f"https://map-mates-profile-api-production.up.railway.app/socials/received_requests/{self_id}"
    response = requests.get(url_incoming_requests)

    return response

def get_friends(self_id: int):
    url_get_friends = f"https://map-mates-profile-api-production.up.railway.app/socials/get_friends/{self_id}"
    response = requests.get(url_get_friends)

    return response


def full_test():
    response_create = create_user(username="Tester", email="test@test.test", password="test123")
    response_login = login_user(username="Tester", password="test123")
    response_delete = delete_user(username="Tester")
    response_add_location = add_location(user_id=1, latitude=random.randrange(10, 60), longitude=random.randrange(10, 60))
    response_get_location = get_last_location(user_id=1)
    response_search_user = search_user(search="momo", user_id=1)
    response_send_request = send_request(sender_id=3, receiver_id=1)
    response_accept_request = accept_request(self_user_id=1, sender_user_id=3)
    response_send_request = send_request(sender_id=15, receiver_id=1)
    response_deny_request = deny_request(self_user_id=1, sender_user_id=15)
    response_get_outgoing = get_outgoing_requests(self_id=3)
    response_get_incoming = get_incoming_requests(self_id=26)
    response_get_friends = get_friends(self_id=15)



    print(f"Create User Status: {response_create.status_code} \nMessage: {response_create.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Login User Status: {response_login.status_code} \nMessage: {response_login.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Delete User Status: {response_delete.status_code} \nMessage: {response_delete.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Add Location Status: {response_add_location.status_code} \nMessage: {response_add_location.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Got Location Status: {response_get_location.status_code} \nMessage: {response_get_location.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Search User Status: {response_search_user.status_code} \nMessage: {response_search_user.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Send Request Status: {response_send_request.status_code} \nMessage: {response_send_request.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Accept Request Status: {response_accept_request.status_code} \nMessage: {response_accept_request.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Deny Request Status: {response_deny_request.status_code} \nMessage: {response_deny_request.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Outgoing Requests Status: {response_get_outgoing.status_code} \nMessage: {response_get_outgoing.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Incoming Requests Status: {response_get_incoming.status_code} \nMessage: {response_get_incoming.text}")
    print("-------------------------------------------------------------------------------------------------")
    print(f"Get friends Status: {response_get_friends.status_code} \nMessage: {response_get_friends.text}")

if __name__ == "__main__":
   # response = delete_user("Stine")
   # print(f"Status: {response.status_code} \nMessage: {response.text}")
   full_test()
   #response_get_location = get_last_location(user_id=1) 
   #print(f"Status: {response_get_location.status_code} \nMessage: {response_get_location.text}")