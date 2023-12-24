import pymongo
from pymongo.encryption import ClientEncryption
print
# Set up the key vault and data key providers.
key_vault_namespace = "encryption.__keyVault"
kms_providers = {
    "aws": {
        "accessKeyId": "<YOUR_ACCESS_KEY_ID>",
        "secretAccessKey": "<YOUR_SECRET_ACCESS_KEY>",
    }
}

# Create a ClientEncryption instance.
client_encryption = ClientEncryption(
    kms_providers=kms_providers,
    key_vault_namespace=key_vault_namespace,
    mongodb_client=pymongo.MongoClient("<ATLAS_CONNECTION_STRING>"),
)

# Create a MongoClient instance with auto encryption options.
client = pymongo.MongoClient(
    "<ATLAS_CONNECTION_STRING>",
    auto_encryption_opts={
        "key_vault_namespace": key_vault_namespace,
        "kms_providers": kms_providers,
        "schema_map": {
            "cisco.customers": {
                "bsonType": "object",
                "encryptMetadata": {
                    "keyId": ["local"]
                },
                "properties": {
                    "name": {
                        "bsonType": "string",
                        "encrypt": {
                            "keyId": ["local"]
                        }
                    },
                    "email": {
                        "bsonType": "string",
                        "encrypt": {
                            "keyId": ["local"]
                        }
                    }
                }
            }
        }
    }
)

# Insert an encrypted document.
customer = {
    "name": "Alice",
    "email": "alice@example.com",
}
encrypted_customer = client_encryption.encrypt(
    customer, key_alt_names=["local"])
result = client["cisco"]["customers"].insert_one(encrypted_customer)
print(result.inserted_id)

# Retrieve the encrypted document and decrypt it.
retrieved_customer = client["cisco"]["customers"].find_one(
    {"_id": result.inserted_id})
decrypted_customer = client_encryption.decrypt(retrieved_customer)
print(decrypted_customer)
