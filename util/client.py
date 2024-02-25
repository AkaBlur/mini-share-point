"""This file implements a simple client for authentication with the Server endpoint"""

import base64
import binascii
import dataclasses
import json
import logging
from nacl.public import PrivateKey, PublicKey, Box
from nacl.exceptions import CryptoError
import os
import requests
import sys
import time


@dataclasses.dataclass
class KeyStorage:
    ClientSecret: str
    ClientSK: PrivateKey
    ServerPK: PublicKey


def check_file_exist(Filepath: str) -> bool:
    """Utility function to check if a file exists"""
    if os.path.exists(Filepath) and os.path.isfile(Filepath):
        return True

    else:
        logging.warning("File not found: %s", Filepath)
        return False


def load_keystore(
    ClientSecret: str, ClientKeyFile: str, ServerPubFile: str
) -> KeyStorage:
    """Load all necessary key files for operation"""
    RetStore = KeyStorage

    # client hex secret
    if not check_file_exist(ClientSecret):
        logging.critical("Client secret file <%s> not found!", ClientSecret)
        exit(1)

    with open(ClientSecret) as Keyfile:
        RetStore.ClientSecret = Keyfile.readline()

    # client secret key
    if not check_file_exist(ClientKeyFile):
        logging.critical("Client private keyfile <%s> not found!", ClientKeyFile)
        exit(1)

    with open(ClientKeyFile, "r") as Keyfile:
        KeyStr = Keyfile.readline()
        Keybytes: bytes

        try:
            Keybytes = base64.b64decode(KeyStr)

        except binascii.Error:
            logging.critical("Client private keyfile <%s> malformed!", ClientKeyFile)
            exit(1)

        if len(Keybytes) != 32:
            logging.critical("Client private keyfile <%s> malformed!", ClientKeyFile)
            exit(1)

        RetStore.ClientSK = PrivateKey(Keybytes)

    # server public key
    check_file_exist(ServerPubFile)
    with open(ServerPubFile, "r") as Keyfile:
        KeyStr = Keyfile.readline()
        Keybytes: bytes

        try:
            Keybytes = base64.b64decode(KeyStr)

        except binascii.Error:
            logging.critical("Server public keyfile <%s> malformed!", ServerPubFile)
            exit(1)

        if len(Keybytes) != 32:
            logging.critical("Server public keyfile <%s> malformed!", ServerPubFile)
            exit(1)

        RetStore.ServerPK = PublicKey(Keybytes)

    return RetStore


def prepare_payload(KeyStore: KeyStorage, RemoteMethod: str) -> dict[str, str]:
    """Generate a JSON-like dictionary to send as request to the server"""
    # encrypted message
    MsgBox = Box(KeyStore.ClientSK, KeyStore.ServerPK)
    SecMsgBytes = KeyStore.ClientSecret.encode("utf-8")
    MsgEncrypt = MsgBox.encrypt(SecMsgBytes)

    # crc32 encrypted message
    CRCBox = Box(KeyStore.ClientSK, KeyStore.ServerPK)
    # calculated crc32 from actual key
    SecCRC = binascii.crc32(SecMsgBytes)
    CRCEncrypt = CRCBox.encrypt(SecCRC.to_bytes((SecCRC.bit_length() + 7) // 8, "big"))
    # current timestamp
    TimeBox = Box(KeyStore.ClientSK, KeyStore.ServerPK)
    SecTime = int(time.time())
    TimeEncrypt = TimeBox.encrypt(
        SecTime.to_bytes((SecTime.bit_length() + 7) // 8, "big")
    )

    # encrypted remote function call
    FuncBox = Box(KeyStore.ClientSK, KeyStore.ServerPK)
    FuncEncrypt = FuncBox.encrypt((RemoteMethod).encode("utf-8"))

    # starting here: anything sent could be dangerous!
    StrEncrypt = base64.urlsafe_b64encode(MsgEncrypt).decode("utf-8")
    StrCRC = base64.urlsafe_b64encode(CRCEncrypt).decode("utf-8")
    StrTime = base64.urlsafe_b64encode(TimeEncrypt).decode("utf-8")
    StrFunc = base64.urlsafe_b64encode(FuncEncrypt).decode("utf-8")

    Data = {"id": StrEncrypt, "check": StrCRC, "ts": StrTime, "entry": StrFunc}

    return Data


def send_auth(URL: str, Payload: dict[str, str]) -> str:
    """Sends the payload to the server and returns the awnser if successful"""
    Req = requests.post(
        URL, data=json.dumps(Payload), headers={"Content-Type": "application/json"}
    )

    if Req.status_code == 401:
        logging.warning("Unauthorized request made one: %s", URL)
        return

    elif not Req.status_code == 200:
        logging.warning("Request error [%d] on %s:", Req.status_code, URL)
        return

    EncryptResponse = ""

    try:
        JsonReq = Req.json()

        if "value" in JsonReq:
            EncryptResponse = JsonReq["value"]

    except requests.exceptions.JSONDecodeError as e:
        logging.warning("Could not decode JSON response from server!")
        print(e)

    if EncryptResponse == "":
        logging.critical("Empty response from server!")
        exit(1)

    return EncryptResponse


def decrypt_awnser(Data: str, KeyStore: KeyStorage) -> str:
    """Decrypt the resulting message from the server"""
    RespEncrypt = base64.urlsafe_b64decode(Data)
    ResponseBox = Box(KeyStore.ClientSK, KeyStore.ServerPK)
    Response = ""

    try:
        ResBytes = ResponseBox.decrypt(RespEncrypt)
        Response = ResBytes.decode("utf-8")

    except CryptoError:
        logging.critical("Server decryption error!")
        exit(1)

    return Response


if __name__ == "__main__":
    logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level="INFO")

    # Read in URL to connect to
    if len(sys.argv) != 2:
        print("Usage:\n\tclient.py <URL>")
        exit(1)
    URL = sys.argv[1]

    # BASIC CLIENT AUTH CHAIN
    # load the default keys for the client
    DefaultStorage = load_keystore("client.secret", "client.key", "server.pub")
    # Generate the payload with a given remote function
    PL = prepare_payload(DefaultStorage, "time_test")
    # Send request to the server
    EncryptAwnser = send_auth(URL, PL)
    # Decrypt the response
    DecryptAwnser = decrypt_awnser(EncryptAwnser, DefaultStorage)

    logging.info("%s", DecryptAwnser)
