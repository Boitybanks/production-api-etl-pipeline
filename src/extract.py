import requests

BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

PARAMS = {
    "ids": "bitcoin,ethereum,solana,xrp,dogecoin,cardano",
    "vs_currencies": "usd"
}

response = requests.get(BASE_URL, params=PARAMS)

print(f"Status Code: {response.status_code}")
print(response.json())