## Keyvault client

The keyvault client will

* Search and retrieve secrets
* Delete individual secrets
* Check what subscriptions you have access to.
* Check for all keyvaults in those subscriptions.


### Requirements

**For the binary:**

Set the file as executable and run.

**For the Python script:**

Python 3 and a few azure modules are needed. Assuming you already have python3 and pip3 on your system do the following:

```
sudo pip3 install azure-keyvault==1.0.0 azure-mgmt-keyvault azure-mgmt-resource jmespath
```

**Note:** azure-keyvault needs to be at 1.0.0. The latest (1.1.0) is buggy.

If python complains that python.h is missing you might need to install the python3-dev package on your system. e.g `sudo apt install python3-dev`

Now either set the script as executable and run or run `python3 kv-client.py` 


### Passing credentials

kv-client needs to be passed service principle credentials.
There area a few ways to do this.

**Directly on the cli:**
```
kv-client --clientid <id> --secret <client-secret> --tenant <tenent-id>
```

**Or with a credentials file.**

The file needs to be json with the following format.

```
{
    "clientId": "<id>",
    "clientSecret": "<client-secret>",
    "tenantId": "<tenent-id>"
}
```

The file location can be set by the following methods.

Command line argument:

```
kv-client --credsfile <file-path>
```

The following location will be automatically checked if no cli arguments are provided:

```
~/.azure/keyvault.json
```


Finally the file path can be set in the environment variable `
AZURE_AUTH_LOCATION`

### Usage

After  startup you can search for secrets.

When searching you can use as many keywords as you like e.g:

```
Enter secret to search for: postgres build ie


1. postgres-buildinghoursservice-co-ie
2. postgres-buildinghoursservice-du-ie
3. postgres-buildinghoursservice-ld-ie
4. postgres-buildinghoursservice-oy-ie

 0. Return to search
-1. Delete Secrets


Choose secret:

```

After searching you can choose a secret and it will be retrived:

```
Choose secret: 2

postgres-buildinghoursservice-du-ie:
b3phWHVLUWssdf34DFGdhqrgk=

```

You can also switch to deletion mode by entering `-1`:
```
choose secret: -1
Select secret to delete: 3

WARNING: The secret postgres-buildinghoursservice-du-ie will be deleted

Are you sure you want to continue N/y:
``` 
Note that you can only delete one secret at a time and will need to switch back to delete mode for each one.

Finally you can return to the search mode:
```
Choose secret: 0

Enter secret to search for:
```