import binascii
import base64
import logging
from nacl.public import PublicKey
from glob import glob

from . import util

"""Stored public keys from clients"""
ClientKeys: list[PublicKey] = []
__ClientStrings = []


def load_client_secret(ClientRegister: str) -> bool:
    """Load all client secret keys from register file"""
    if not util.check_file_exist(ClientRegister):
        logging.getLogger(__name__).critical(
            "Client secretfile <%s> not found!", ClientRegister
        )
        return False

    with open(ClientRegister, "r") as File:
        Line = File.readline()

        while Line:
            Line = Line.split("\n")[0]
            Line = Line.split("\r")[0]

            __ClientStrings.append(Line)
            logging.getLogger(__name__).debug("Added client secret: %s", Line)

            Line = File.readline()

        return True


def load_client_keys(ClientKeyPath: str):
    """Load all client keys from directory"""
    Keyfiles = glob(f"{ClientKeyPath}/client_*.pub")
    for Keyfile in Keyfiles:
        if not util.check_file_exist(Keyfile):
            logging.getLogger(__name__).warning(
                "File <%s> not a keyfile! Please remove from key location: %s",
                Keyfile,
                ClientKeyPath,
            )
            continue

        # client public key
        with open(Keyfile, "r") as File:
            PKStr = File.readline()
            PKBytes: bytes

            try:
                PKBytes = base64.b64decode(PKStr)

            except binascii.Error:
                logging.getLogger(__name__).error(
                    "Client public keyfile corrupt! Ignoring keyfile: %s", Keyfile
                )
                continue

            if len(PKBytes) != 32:
                logging.getLogger(__name__).error(
                    "Client public keyfile corrupt! Ignoring keyfile: %s", Keyfile
                )
                continue

            PKClient = PublicKey(PKBytes)
            ClientKeys.append(PKClient)
            logging.getLogger(__name__).debug("Loaded client keyfile: %s", Keyfile)


def check_client_register(Secret: str) -> bool:
    """Checks if a client secret is registered"""
    if Secret in __ClientStrings:
        return True

    return False
