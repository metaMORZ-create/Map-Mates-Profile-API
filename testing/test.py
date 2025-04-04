import requests

url_register = "https://map-mates-profile-api-production.up.railway.app/register"
url_login = "https://map-mates-profile-api-production.up.railway.app/login"
data_create_user = {"username": "Moritz", "email": "baarsmoritz796@gmail.com", "password": "test"}
data_login_user = {"username": "Moritz", "password": "test"}

response = requests.post(url_register, json=data_create_user)
print(response.status_code)
print(response.text)