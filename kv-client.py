#!/usr/bin/python3
from azure.mgmt.resource import SubscriptionClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.keyvault.models.key_vault_error_py3 import KeyVaultErrorException
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from urllib.parse import urlparse
import os, json, jmespath, base64, argparse, sys

parser = argparse.ArgumentParser()
parser.add_argument("--clientid", help="Service principle client ID")
parser.add_argument("--secret", help="Service principle client secret")
parser.add_argument("--tenant", help="AD tenent ID")
parser.add_argument("--credsfile", help="json file with keyvault credentials")
args = parser.parse_args()

# Get credentails 
# TODO This works but it not very readble
# Rework with a cleaner flow.
if not all((args.clientid, args.secret, args.tenant)):
    if args.credsfile and os.path.isfile(args.credsfile):
        creds_file = args.credsfile
    elif 'AZURE_AUTH_LOCATION' in os.environ:
        creds_file = os.environ['AZURE_AUTH_LOCATION']
    elif 'AZURE_AUTH_LOCATION' not in os.environ:
        homedir = os.path.expanduser("~")
        if os.path.isfile(homedir + '/.azure/keyvault.json'):
            creds_file = homedir + '/.azure/keyvault.json'
        else:
            print('\nNo credentials found. See readme.md for options.\n')
            sys.exit()

    with open(creds_file) as json_data:
        creds = json.load(json_data)

    az_client_id = creds['clientId']
    az_secret = creds['clientSecret']
    az_tenant = creds['tenantId']
else:
    if args.credsfile is not None:
        print('\n--credsfile cannot be used at the same time as other credential agruments.\n')
        sys.exit()

    az_client_id = args.clientid
    az_secret = args.secret
    az_tenant = args.tenant

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

def delete_secret(secret_id):
    url = urlparse(secret_id)

    secret_value = keyvault_client.delete_secret(
        'https://' + url.netloc,
        os.path.basename(secret_id),
        ''
    )

# Check if a secret is base64 encoded
def is_base64(s):
    #base64decode/encode wants a byte sequence not a string
    s = (s.encode('utf-8'))
    
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False

def choose_secret(secrets_ids, message):
    try:
        user_input = int(input(message))
    except ValueError:
        print(bcolors.YELLOW + 'Input needs to be a number\n' + bcolors.RESET)
        return 'not_int'
    
    if user_input > len(secrets_ids) or user_input < -1:
        print(bcolors.YELLOW + 'Select from the range above\n' + bcolors.RESET)
        return 'not_int'
    
    return user_input

def print_selection_list(secrets_ids):
    for index, item in enumerate(secrets_ids):
        print('{}. {}'.format(index + 1, os.path.basename(item)))
    print('\n 0. Return to search')
    print('-1. Delete Secrets\n\n')

# Get list of subscription id's
print('\nChecking subscriptions.........', end='', flush=True)
subscription_client = SubscriptionClient(credentials)
subscriptions = subscription_client.subscriptions.list()
for item in subscriptions:
    item = item.as_dict()
    subscription_ids.append(item['subscription_id'])
print(bcolors.GREEN + 'OK' + bcolors.RESET)

# Get keyvaults in all subscriptions
print('Retrieving list of keyvaults...', end='', flush=True)
for item in subscription_ids:
    kv_mgmt_client = KeyVaultManagementClient(credentials, item)
    kv = kv_mgmt_client.vaults.list()
    for item in kv:
        item = item.as_dict()
        keyvault_list.append(item['name'])
print(bcolors.GREEN + 'OK\n' + bcolors.RESET)

# Get list of secrets from all kevaults in parrelel
keyvault_client = KeyVaultClient(KeyVaultAuthentication(auth_callback))
pool = ThreadPool()
s =  pool.map(list_secrets, keyvault_list)
pool.close()
pool.join()
# flatten the list of lists returned by pool.map
l = [item for sublist in s for item in sublist]
print('Loaded', len(l), 'secrets')

# Main loop
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

    print_selection_list(secrets_ids)

    # retrieve/delete secret loop
    while True:

        user_input = choose_secret(secrets_ids,'choose secret: ')

        if user_input == 'not_int':
            continue
        # return to search
        elif user_input == 0:
            break
        # delete a secret
        elif user_input == -1:

            user_input = choose_secret(secrets_ids, 'Select secret to delete: ')
            if user_input == 'not_int':
                continue

            print('\n{0}WARNING:{1} The secret {0}{2}{1} will be deleted'.format(
                bcolors.YELLOW, bcolors.RESET, os.path.basename(secrets_ids[user_input - 1])))

            delete_input = input('\nAre you sure you want to continue N/y: ')
            print('\n')
            if delete_input == 'y':
                # delete from keyvault
                # TODO do the delete in a try/except                
                delete_secret(secrets_ids[user_input -1])
                del_secret_name = os.path.basename(secrets_ids[user_input - 1])
                # delete from the main list and selection list
                for i, dic in enumerate(l):
                    if dic['id'] == secrets_ids[user_input - 1]:
                        del(l[i])
                del(secrets_ids[user_input - 1])
                # print the updated selection list
                print_selection_list(secrets_ids)
                print(bcolors.GREEN + 'Successfully deleted ' +
                    del_secret_name + bcolors.RESET + '\n')
            else:
                continue   
        else:
            print('\n{}:'.format(os.path.basename(secrets_ids[user_input - 1])))
            secret = get_secret(secrets_ids[user_input - 1])
            print(bcolors.GREEN + secret + bcolors.RESET + '\n')

            if is_base64(secret):
                print("This secret is base64 encoded. Here's the decoded version:")
                print(bcolors.GREEN + base64.b64decode(secret).decode() + bcolors.RESET + '\n')
            print('----------------------------------\n\n')