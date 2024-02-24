import base64
import binascii
import json
import logging
from nacl.public import PrivateKey, PublicKey, Box
from nacl.exceptions import CryptoError
import os
import requests
import sys
import time


ClientSecret =  "util/client.secret"
ClientKeyFile = "util/client.key"
ServerPubFile = "util/server.pub"


def check_file_exist(Filepath: str) -> bool:
    if os.path.exists(Filepath) and os.path.isfile(Filepath):
        return True

    else:
        logging.warning("File not found: %s", Filepath)
        return False


def send_auth(URL: str):
    SecKey = ""
    SKClient = None
    PKServer = None

    # client hex secret
    if not check_file_exist(ClientSecret):
        logging.critical("Client secret file <%s> not found!", ClientSecret)
        exit(1)

    with open(ClientSecret) as Keyfile:
        SecKey = Keyfile.readline()

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

        SKClient = PrivateKey(Keybytes)

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

        PKServer = PublicKey(Keybytes)

    # encrypted message
    MsgBox = Box(SKClient, PKServer)
    SecMsgBytes = SecKey.encode("utf-8")
    MsgEncrypt = MsgBox.encrypt(SecMsgBytes)

    # crc32 encrypted message
    CRCBox = Box(SKClient, PKServer)
    # calculated crc32 from actual key
    SecCRC = binascii.crc32(SecMsgBytes)
    CRCEncrypt = CRCBox.encrypt(SecCRC.to_bytes((SecCRC.bit_length() + 7) // 8, "big"))
    # current timestamp
    TimeBox = Box(SKClient, PKServer)
    SecTime = int(time.time())
    TimeEncrypt = TimeBox.encrypt(SecTime.to_bytes((SecTime.bit_length() + 7) // 8, "big"))

    # encrypted remote function call
    FuncBox = Box(SKClient, PKServer)
    FuncEncrypt = FuncBox.encrypt(("time_test").encode("utf-8"))

    # starting here: anything sent could be dangerous!
    StrEncrypt = base64.urlsafe_b64encode(MsgEncrypt).decode("utf-8")
    StrCRC = base64.urlsafe_b64encode(CRCEncrypt).decode("utf-8")
    StrTime = base64.urlsafe_b64encode(TimeEncrypt).decode("utf-8")
    StrFunc = base64.urlsafe_b64encode(FuncEncrypt).decode("utf-8")

    Data = {
        "id": StrEncrypt,
        "check": StrCRC,
        "ts": StrTime,
        "entry": StrFunc
    }

    Req = requests.post(URL,
                        data = json.dumps(Data),
                        headers = {"Content-Type": "application/json"})

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

    RespEncrypt = base64.urlsafe_b64decode(EncryptResponse)
    ResponseBox = Box(SKClient, PKServer)
    Response = ""

    try:
        ResBytes = ResponseBox.decrypt(RespEncrypt)
        Response = ResBytes.decode("utf-8")

    except CryptoError:
        logging.critical("Server decryption error!")
        exit(1)

    logging.info("%s", Response)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:\n\tclient.py <URL>")
        exit(1)

    logging.basicConfig(format = "[%(asctime)s] %(levelname)s: %(message)s",
                        level = "INFO")

    URL = sys.argv[1]
    send_auth(URL)
