import requests, jwt

HANKO_API_URL = "https://e3c4803f-48cc-4b62-9ac5-2aa02444ba51.hanko.io"

AUDIENCE = "localhost"
app_url = "http://localhost"

jwks_url = f"{HANKO_API_URL}/.well-known/jwks.json"
jwks_response = requests.get(jwks_url)
jwks_data = jwks_response.json()
public_keys = {}
for jwk in jwks_data["keys"]:
    kid = jwk["kid"]
    public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)