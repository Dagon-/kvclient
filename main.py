from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.common.credentials import ServicePrincipalCredentials
import json, jmespath, base64
import os, pprint

az_client_id = ''
az_secret = ''
az_tenant = ''
keyvault_uri = CRED
secrets = []

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[0;93m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'  # text reset
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BACKGROUND = '\033[100m'
    BACKGROUND_GRAY = '\033[48;5;235m'


def auth_callback(server, resource, scope):
    credentials = ServicePrincipalCredentials(
        client_id = az_client_id,
        secret = az_secret,
        tenant = az_tenant,
        resource = "https://vault.azure.net"
    )
    token = credentials.token
    return token['token_type'], token['access_token']

# Pass the complte secret id
def getSecret(secret_id):
    secret_value = client.get_secret(
        keyvault_uri,
        os.path.basename(secret_id),
        ''
    )
    return secret_value.value

# Check if a secret is bas64 encoded
def isBase64(s):
    #base64decode/encode wants a byte sequence not a string
    s = (s.encode('utf-8'))

    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False

client = KeyVaultClient(KeyVaultAuthentication(auth_callback))

secrets_objects = client.get_secrets(keyvault_uri)

#Add all secrets to a list of dicts
print('Loading secrets...')
for item in (secrets_objects):
    secrets.append(item.as_dict())
    #print('.', end='', flush=True)

print('Loaded', len(secrets), 'secrets')

while True:
    print('\nEnter secret to search for: ', end='')
    user_input = input()
    print('\n')

    # Pull out all the secret id's that match the search value
    query = "[*].id | [?contains(@,'" + user_input + "') == `true`]"
    search_result = jmespath.search(query, secrets)

    for index, item in enumerate(search_result):
        print('{}. {}'.format(index + 1, os.path.basename(item)))
    print('\n')

    print('Choose secret: ', end='')
    user_input = int(input())

    secret = getSecret(search_result[user_input - 1])
    print(bcolors.GREEN + secret + bcolors.RESET)


    if isBase64(secret):
        print("\nThis secret is base64 encoded. Here's the decoded version:")
        print(bcolors.GREEN + base64.b64decode(secret).decode() + bcolors.RESET + '\n')
