from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class get_secret:
    def __init__(self):
        #self.secret_name = secret_name
        self.credential = DefaultAzureCredential()
        self.vault_url = "https://keyvault-msfnex20-fx-dev.vault.azure.net/"
        self.client =  SecretClient(vault_url=self.vault_url, credential=self.credential)

    def get_secret_value(self,secret_name): 
        retrieved_secret = self.client.get_secret(secret_name)
        return retrieved_secret.value
        #print("Secret value:", retrieved_secret.value)