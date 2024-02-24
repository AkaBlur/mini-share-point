import configparser
from glob import glob
import logging
import os
import sys


__config = configparser.ConfigParser()
__configPath = os.getenv("MSP_CONFIG_PATH", "config/config.ini")


def load_config():
    """Load config file from default location"""
    if os.path.exists(__configPath) and os.path.isfile(__configPath):
        __config.read(__configPath)

    else:
        logging.critical("Could not find config file <%s> in default location!", __configPath)
        exit(1)


def read_config(Section: str, Key: str, Fallback: str) -> str:
    """Read a value from the config"""
    Val = __config.get(Section, Key, fallback=Fallback)

    return Val


def append_client(ClientPublicKey: str, ClientRegFile: str, ClientKeyPath: str) -> str:
    """Append a client public key to the keystore. Generates the client secret hex"""
    IsClientRegFile = os.path.exists(ClientRegFile) and os.path.isfile(ClientRegFile)
    IsClientKeyStore = os.path.exists(ClientKeyPath) and os.path.isdir(ClientKeyPath)

    if not IsClientRegFile:
        logging.critical("Client secret-file <%s> could not be loaded!", ClientRegFile)
        return "NO_APPEND"

    if not IsClientKeyStore:
        logging.critical("Client key storage <%s> not found!", ClientKeyPath)
        return "NO_APPEND"

    Keyfiles = glob(f"{ClientKeyPath}/client_*.pub")
    NextKey = 1

    if len(Keyfiles) > 0:
        Keyfiles = sorted(Keyfiles)
        LastKey = Keyfiles[-1]
        LastKey: str = os.path.basename(LastKey)
        NextKey = int(LastKey.split(".")[0].split("_")[-1]) + 1

    with open(f"{ClientKeyPath}/client_{NextKey}.pub", "w") as File:
        File.write(ClientPublicKey)

    BytesClientSecret = os.urandom(64)
    IntL = [int(byte) for byte in BytesClientSecret]
    StrClientSecret = ("").join([f"{val:02x}" for val in IntL])

    with open(ClientRegFile, "a") as File:
        File.write(StrClientSecret)
        File.write("\n")

    return StrClientSecret


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.INFO
    )
    load_config()
    ClientRegFile = read_config("Clients", "Register", "sec/clients.dev")
    ClientKeyStore = read_config("Clients", "Keypath", "sec")

    if len(sys.argv) != 2:
        print("Usage: append_client <CLIENT_PUB_KEY>\n")
        print("\CLIENT_PUB_KEY:")
        print("\t\t- client public key, formatted as base64-string")
        exit(1)

    ClientStr = append_client(sys.argv[1], ClientRegFile, ClientKeyStore)

    if ClientStr == "NO_APPEND":
        logging.critical("Error while appending client!")
        exit(1)

    logging.info("Client Hex Secret: %s", ClientStr)
