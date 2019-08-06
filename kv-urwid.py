from azure.mgmt.resource import SubscriptionClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.keyvault.models.key_vault_error_py3 import KeyVaultErrorException
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from urllib.parse import urlparse
import os
import sys
import json
import argparse
import urwid
import jmespath
import collections

from custom_widgets import MyButton
#from azurecalls import get_secrets 

class bcolors():
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[0;93m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BACKGROUND = '\033[100m'
    BACKGROUND_GRAY = '\033[48;5;235m'

class kvDisplay():

    PALETTE = [
        ('input expr', 'black,bold', 'light gray'),
        ('bigtext', 'white', 'black'),
        ('highlight', 'white', 'dark gray')
    ]

    def __init__(self, output_mode='result'):
        self.choices = master_list
        self.view = None
        self.output_mode = output_mode
        self.last_result = None

    def _get_font_instance(self):
        return urwid.get_all_fonts()[-2][1]()

    def handle_enter(self, c, other):
        self.secret_details.set_text(c + ' select worked!')

    def handle_scroll(self, listBox):
        index = listBox.focus_position
        #widget = listBox.body[index]
        self.secret_details.set_text("Index of selected item: " + str(index))

    def listbox_secrets(self, choices):
        #body = [urwid.Divider()]
        body = []

        for c in choices:
            secret_name = c['id'].rsplit('/', 1)[-1] # get the secret name from the url
            button = MyButton(secret_name)
            urwid.connect_signal(button, 'click', self.handle_enter, user_args = [secret_name])
            body.append(urwid.AttrMap(button, None, focus_map = 'highlight'))

        walker = urwid.SimpleListWalker(body)
        listBox = urwid.ListBox(walker)
        
        # pass the whole listbox to the handler
        urwid.connect_signal(walker, "modified", self.handle_scroll, user_args = [listBox] )


        return listBox, walker



    def _create_view(self):

        ### header
        self.input_expr = urwid.Edit(('input expr', 'Search secrets: '))

        sb = urwid.BigText('KV Client', self._get_font_instance())
        sb = urwid.Padding(sb, 'center', None)
        sb = urwid.AttrWrap(sb, 'bigtext')
        sb = urwid.Filler(sb, 'top', None, 5)
        self.status_bar = urwid.BoxAdapter(sb, 5)

        div = urwid.Divider()
        self.header = urwid.Pile([self.status_bar, div,
            urwid.AttrMap(self.input_expr, 'input expr'), div],
            focus_item=2)

        urwid.connect_signal(self.input_expr, 'postchange', self._on_search)

        ### content

        self.left_content, self.list_walker = self.listbox_secrets(self.choices)
        self.left_content = urwid.LineBox(self.left_content, title='Secret list')

        self.secret_details = urwid.Text("start_text")
        self.secret_details_list = [div, self.secret_details]

        self.right_content = urwid.ListBox(self.secret_details_list)
        self.right_content = urwid.LineBox(self.right_content, title='Secret details')

        self.content = urwid.Columns([('weight',1.5, self.left_content), self.right_content])
        
        ### footer
        self.footer = urwid.Text("Status: " + str(len(self.list_walker.contents)))


        ### frame config
        self.view = urwid.Frame(body=self.content, header=self.header,
                                footer=self.footer, focus_part='header')


    def _on_search(self, widget, text):
        # delete everything in the list bar the divider at index 0
        del self.list_walker.contents[1:len(self.list_walker.contents)]

        if not self.input_expr.get_edit_text(): # if the search box is blank
            for c in master_list:
                secret_name = c['id'].rsplit('/', 1)[-1] # get the secret name from the url
                button = MyButton(secret_name)
                urwid.connect_signal(button, 'click', self.handle_enter, user_args = [secret_name])
                self.list_walker.contents.append(urwid.AttrMap(button, None, focus_map = 'highlight'))
            self.footer.set_text("Status: " + str(len(self.list_walker.contents))) 
        else:
            for c in master_list:
                secret_name = c['id'].rsplit('/', 1)[-1] # get the secret name from the url
                if self.input_expr.get_edit_text() in secret_name:
                    button = MyButton(secret_name)
                    urwid.connect_signal(button, 'click', self.handle_enter, user_args = [secret_name])
                    self.list_walker.contents.append(urwid.AttrMap(button, None, focus_map = 'highlight'))
            self.footer.set_text("Status: " + str(len(self.list_walker.contents)))



    def main(self, screen=None):
        self._create_view()
        self.loop = urwid.MainLoop(self.view, self.PALETTE,
                                   unhandled_input=self.unhandled_input,
                                   screen=screen)
        self.loop.screen.set_terminal_properties(colors=256)
        self.loop.run()


    def unhandled_input(self, key):
        if key == 'esc':
            raise urwid.ExitMainLoop()
        elif key == 'tab':
            current_pos = self.view.focus_position
            if current_pos == 'header':
                self.view.focus_position = 'body'
            else:
                self.view.focus_position = 'header'

            


def main(master_list):

    screen = urwid.raw_display.Screen()
    display = kvDisplay(master_list)
    display.main(screen=screen)






#############################




subscription_ids = []
keyvault_list = []

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
        elif 'is not authorized and caller is not a trusted service' in err.message:
            print('Loading secrets from {:.<25}'.format(keyvault_list),  end='', flush=True)
            print(bcolors.YELLOW + err.message + bcolors.RESET)
        else:
            print('Loading secrets from {:.<25}'.format(keyvault_list),  end='', flush=True)
            print(bcolors.RED + err.message + bcolors.RESET)

    return secrets

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


# Get list of secrets from all kevaults in parallel
keyvault_client = KeyVaultClient(KeyVaultAuthentication(auth_callback))
pool = ThreadPool()
s =  pool.map(list_secrets, keyvault_list)
pool.close()
pool.join()
# flatten the list of lists returned by pool.map
master_list = [item for sublist in s for item in sublist]
print('Loaded', len(master_list), 'secrets')


if __name__ == '__main__':
   sys.exit(main(master_list))