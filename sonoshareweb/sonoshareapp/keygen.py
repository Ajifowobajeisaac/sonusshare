import jwt
import time

# Set the necessary claims and values
team_id = '732N38L7AM'
key_id = '247CZ32RAC'
issuer = team_id
issued_at = int(time.time())
expiration_time = issued_at + 15777000  # 6 months in seconds

# Set the headers
headers = {
    'alg': 'ES256',
    'kid': key_id
}

# Set the payload
payload = {
    'iss': issuer,
    'iat': issued_at,
    'exp': expiration_time
}

# Read the private key file
with open('/root/apple_auth_key.p8', 'r') as key_file:
    private_key = key_file.read()

# Generate the developer token
developer_token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)

# Print the token
print(developer_token)
