from azure.mgmt.resource import SubscriptionClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.keyvault.models.key_vault_error_py3 import KeyVaultErrorException
from urllib.parse import urlparse
import os, json, jmespath, base64

az_client_id = CRED
az_secret = CRED
az_tenant = CRED
credentials = ServicePrincipalCredentials(
    client_id = az_client_id,
    secret = az_secret,
    tenant = az_tenant
)

secrets = []
subscription_ids = []
keyvault_list = []

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

# Get tokens for keyvault access
def auth_callback(server, resource, scope):
    credentials = ServicePrincipalCredentials(
        client_id = az_client_id,
        secret = az_secret,
        tenant = az_tenant,
        resource = "https://vault.azure.net"
    )
    token = credentials.token
    return token['token_type'], token['access_token']

# Pass the complete secret id
def getSecret(secret_id):
    url = urlparse(secret_id)

    secret_value = keyvault_client.get_secret(
        'https://' + url.netloc,
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

# Get list of subscription id's
print('\nChecking subscriptions...')
subscription_client = SubscriptionClient(credentials)
subscriptions = subscription_client.subscriptions.list()
for item in subscriptions:
    item = item.as_dict()
    subscription_ids.append(item['subscription_id'])

# Get keyvaults in all subscriptions
print('Retrieving list of keyvaults...\n')
for item in subscription_ids:
    kv_mgmt_client = KeyVaultManagementClient(credentials, item)
    kv = kv_mgmt_client.vaults.list()
    for item in kv:
        item = item.as_dict()
        keyvault_list.append(item['name'])        

# Get list of secrets from all kevaults
keyvault_client = KeyVaultClient(KeyVaultAuthentication(auth_callback))
for item in keyvault_list:
    print('Loading secrets from {:.<25}'.format(item),  end='', flush=True)

    try:
        secrets_objects = keyvault_client.get_secrets('https://{}.vault.azure.net/'.format(item))
        for item in (secrets_objects):
            secrets.append(item.as_dict())
        print(bcolors.GREEN + 'OK' + bcolors.RESET)

    except KeyVaultErrorException as err:
        if err.message == '(Forbidden) Access denied':
            print(bcolors.YELLOW + err.message + bcolors.RESET)
        else:
            print(bcolors.RED + err.message + bcolors.RESET)

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
