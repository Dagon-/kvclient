## Keyvault client

The keyvault client will

* Check what subscriptions you have access to.
* Check for all keyvaults in those subscriptions.
* Connect and download a list of screts from those keyvaults.


#### Requirements

Python 3 and a few azure modules are needed. Assumming you already have python3 and pip3 on your system do the following:

```
sudo pip3 install azure-keyvault==1.0.0 azure-mgmt-keyvault azure-mgmt-resource jmespath
```

**Note:** azure-keyvault needs to be at 1.0.0. The latest (1.1.0) is buggy.
If python complains that python.h is missing you might need to install the python3-dev package on your system. e.g `sudo apt install python3-dev`


#### Usage

Open the the file kv-client.py and and credentials at top of the file:

```

az_client_id = '<clientid>'
az_secret = '<secret>'
az_tenant = '<tenetid'
```

Furture versions will try to pull these form the local envoirmenmt or check if you are already logged in to azure'

Make the file executable and run `./kv-client.py`
It will load the secrets, this may take a little while, the backend api is not fast.

To search you can use as many keywords as you like e.g:

```
Enter secret to search for: galera co build


1. galera01-co-ie-jci-ai-db-buildinghoursservice

0. Return to search


Choose secret:

```