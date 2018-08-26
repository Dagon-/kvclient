#!/usr/bin/python3
from azure.mgmt.resource import SubscriptionClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.keyvault.models.key_vault_error_py3 import KeyVaultErrorException
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
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

# Get a list of secrets from a keyvault
def list_secrets(keyvault_list):
    secrets = []
    
    try:
        secrets_objects = keyvault_client.get_secrets(
            'https://{}.vault.azure.net/'.format(keyvault_list)
            )

        for item in (secrets_objects):
            secrets.append(item.as_dict())

        print('Loading secrets from {:.<25}'.format(keyvault_list),  end='', flush=True)
        print(bcolors.GREEN + 'OK' + bcolors.RESET)

    except KeyVaultErrorException as err:
        if err.message == '(Forbidden) Access denied':
            print('Loading secrets from {:.<25}'.format(keyvault_list),  end='', flush=True)
            print(bcolors.YELLOW + err.message + bcolors.RESET)
        else:
            print(bcolors.RED + err.message + bcolors.RESET)

    return secrets

# Pass the complete secret id
def get_secret(secret_id):
    url = urlparse(secret_id)

    secret_value = keyvault_client.get_secret(
        'https://' + url.netloc,
        os.path.basename(secret_id),
        ''
    )
    return secret_value.value

# Check if a secret is bas64 encoded
def is_base64(s):
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

# Get list of secrets from all kevaults in parrelel
keyvault_client = KeyVaultClient(KeyVaultAuthentication(auth_callback))
pool = ThreadPool()
s =  pool.map(list_secrets, keyvault_list)
pool.close()
pool.join()
# flatten the list of lists returned by pool.map
l = [item for sublist in s for item in sublist]
print('Loaded', len(l), 'secrets')

while True:
    # reset secrets variable at the start of the loop
    secrets = l
    print('\nEnter secret to search for: ', end='')
    user_input = input().split()
    print('\n')

    # Filter the list of secrets to those that match the search values
    for item in user_input:
        query = "[?contains(id,'" + item + "') == `true`]"
        secrets = jmespath.search(query, secrets)
    # Pull out the id's
    secrets_ids = jmespath.search('[*].id', secrets)

    for index, item in enumerate(secrets_ids):
        print('{}. {}'.format(index + 1, os.path.basename(item)))
    print('\n0. Return to search\n\n')

    print('Choose secret: ', end='')
    user_input = int(input())
    if user_input == 0:
        continue

    secret = get_secret(secrets_ids[user_input - 1])
    print(bcolors.GREEN + secret + bcolors.RESET)

    if is_base64(secret):
        print("\nThis secret is base64 encoded. Here's the decoded version:")
        print(bcolors.GREEN + base64.b64decode(secret).decode() + bcolors.RESET + '\n')