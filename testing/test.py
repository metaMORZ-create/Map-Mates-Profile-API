import requests

url = "https://map-mates-profile-api-production.up.railway.app/register"
data = {"username": "Moritz", "email": "baarsmoritz79@gmail.com", "name": "Moritz", "last_name": "Baars", "disabled": False, "password": "test"}

response = requests.post(url, json=data)
print(response.status_code)
print(response.json())