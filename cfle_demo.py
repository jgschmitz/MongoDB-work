# cfle_demo.py
# Manual CSFLE (no mongocryptd): insert 1 doc, show decrypted match + raw ciphertext.
from pymongo import MongoClient, WriteConcern
from pymongo.encryption import ClientEncryption, Algorithm
from bson.codec_options import CodecOptions
from bson.binary import STANDARD, Binary
from bson import json_util
from pprint import pprint
import os, random, string, sys

URI = "Atlas Connection String Goes Here"  # <- paste your URI

#database creation and key stuff happens here
DB, COL = "people_demo", "persons"
KV_DB, KV_COL = "encryption", "__keyVault"
KV_NS = f"{KV_DB}.{KV_COL}"
MASTER_KEY = "master-key.bin"
DATA_KEY_ALT = "demo-data-key"

def load_or_make_master_key(path: str) -> bytes:
    if os.path.exists(path):
        b = open(path, "rb").read()
        assert len(b) == 96, "master-key.bin must be exactly 96 bytes"
        return b
    b = os.urandom(96); open(path, "wb").write(b); return b

def get_or_create_datakey(client: MongoClient, kms: dict) -> Binary:
    kv = client[KV_DB][KV_COL].with_options(write_concern=WriteConcern("majority"))
    found = kv.find_one({"keyAltNames": DATA_KEY_ALT})
    if found:
        return found["_id"]  # Binary (UUID subtype 4)
    ce = ClientEncryption(kms, KV_NS, client, CodecOptions(uuid_representation=STANDARD))
    dk = ce.create_data_key("local", key_alt_names=[DATA_KEY_ALT])  # Binary
    ce.close()
    return dk

def enc_det(ce: ClientEncryption, dk: Binary, s: str):
    # Deterministic so equality query works
    return ce.encrypt(s, Algorithm.AEAD_AES_256_CBC_HMAC_SHA_512_Deterministic, key_id=dk)

def dec(ce: ClientEncryption, v):
    return ce.decrypt(v)

def main():
    client = MongoClient(URI)
    kms = {"local": {"key": load_or_make_master_key(MASTER_KEY)}}
    dk  = get_or_create_datakey(client, kms)
    ce  = ClientEncryption(kms, KV_NS, client, CodecOptions(uuid_representation=STANDARD))

    coll = client[DB].get_collection(COL, write_concern=WriteConcern("majority"))

    # Unique marker so you can find this run in Compass
    marker = "probe_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

    # Demo values (feel free to tweak)
    first, last = "Ada", "Lovelace"
    phone, ssn  = "+1-555-123-4567", "111-22-3333"

    # Insert encrypted fields
    doc = {
        "_marker": marker,
        "first": first,
        "last":  last,
        "phone": enc_det(ce, dk, phone),
        "ssn":   enc_det(ce, dk, ssn),  # deterministic for demo; switch to Random for stronger SSN secrecy
    }
    res = coll.insert_one(doc)
    print("Inserted _id:", res.inserted_id)
    print(f"Collections in {DB}:", client[DB].list_collection_names())
    print("Doc count now:", coll.count_documents({"_marker": marker}))

    # Equality query by phone (encrypt the query value first)
    q = {"phone": enc_det(ce, dk, phone), "_marker": marker}
    hits = list(coll.find(q))
    print("\nDecrypted query result:")
    for r in hits:
        r["phone"] = dec(ce, r["phone"])
        r["ssn"]   = dec(ce, r["ssn"])
        pprint(r)

    # Raw ciphertext as stored at rest
    print("\nRaw stored (ciphertext):")
    for r in coll.find({"_marker": marker}):
        print(json_util.dumps(r, indent=2))

    ce.close(); client.close()
    print(f">>> Search in Compass: DB='{DB}', Collection='{COL}', filter {{_marker: \"{marker}\"}}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", repr(e)); sys.exit(1)
