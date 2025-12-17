import requests

url = "http://127.0.0.1:8000/Connexion"

login_data = {
    "email": "TestInscription@gmail.com",
    "motdepasse": "12345"
}

response = requests.post(url, json=login_data)

print(response.status_code)

try:
    print(response.json())
except Exception as e:
    print("Erreur JSON :", e, response.text)
