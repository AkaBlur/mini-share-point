import base64
import binascii
import dataclasses
import enum
import logging
from nacl.public import PrivateKey, PublicKey, Box
from nacl.exceptions import CryptoError
import time

from . import config, sec_client, util


class ReturnCode(enum.Enum):
    CLIENT_AUTH = 0
    NOT_AUTHORIZED = 1


@dataclasses.dataclass
class DecryptedMessage:
    ReturnCode: ReturnCode
    ClientSecret: str
    FunctionCall: str
    ClientKey: PublicKey


__SKStore: list[PrivateKey] = []


def load_server_key(ServerKeypath: str) -> bool:
    """Load the server private keyfile"""
    Keyfile = ServerKeypath + "/server.key"

    if not util.check_file_exist(Keyfile):
        logging.getLogger(__name__).critical(
            "<server.key> not found in given location %s!", ServerKeypath
        )
        return False

    # server secret key
    with open(Keyfile, "r") as File:
        SKStr = File.readline()
        SKBytes: bytes

        try:
            SKBytes = base64.b64decode(SKStr)

        except binascii.Error:
            logging.getLogger(__name__).critical("Server private keyfile corrupt!")
            return False

        if len(SKBytes) != 32:
            logging.getLogger(__name__).critical("Server private keyfile corrupt!")
            return False

        SKServer = PrivateKey(SKBytes)
        __SKStore.append(SKServer)
        logging.getLogger(__name__).debug("Server keyfile loaded")

        return True


def decrypt_remote_call(
    EncodedMsg: str, EncodedCRC: str, EncodedTime: str, EncodedFunc: str
) -> DecryptedMessage:
    """Decrypts a message and returns the sender secret and call function"""
    MsgEncoded = base64.urlsafe_b64decode(EncodedMsg)
    CRCEncoded = base64.urlsafe_b64decode(EncodedCRC)
    TimeEncoded = base64.urlsafe_b64decode(EncodedTime)
    FuncEncoded = base64.urlsafe_b64decode(EncodedFunc)

    ReturnError = DecryptedMessage(ReturnCode.NOT_AUTHORIZED, "", "", None)

    # try decoding the message with every public key
    # check is done via CRC32
    for PKClient in sec_client.ClientKeys:
        MsgBox = Box(__SKStore[0], PKClient)
        CRCBox = Box(__SKStore[0], PKClient)
        TimeBox = Box(__SKStore[0], PKClient)
        FuncBox = Box(__SKStore[0], PKClient)

        SecMsgBytes = b""
        SecCRC = 0
        SecTime = 0
        SecFuncBytes = b""

        try:
            SecMsgBytes = MsgBox.decrypt(MsgEncoded)

        except CryptoError:
            continue

        try:
            SecCRC = int.from_bytes(CRCBox.decrypt(CRCEncoded), "big")

        except CryptoError:
            continue

        try:
            SecTime = int.from_bytes(TimeBox.decrypt(TimeEncoded), "big")

        except CryptoError:
            continue

        try:
            SecFuncBytes = FuncBox.decrypt(FuncEncoded)

        except CryptoError:
            continue

        if SecMsgBytes == b"" or SecCRC == 0 or SecTime == 0 or SecFuncBytes == b"":
            logging.getLogger(__name__).warning("Could not decrypt incoming message!")
            return ReturnError

        # check CRC32 value
        CheckCRC = binascii.crc32(SecMsgBytes)
        logging.getLogger(__name__).debug("Incoming CRC: %s", CheckCRC)
        logging.getLogger(__name__).debug("Checking against: %s", SecCRC)

        # CRC32 values are not identical
        if not CheckCRC == SecCRC:
            continue

        # timestamp for TTL check of request
        CheckTime = int(time.time())
        Delta = abs(CheckTime - SecTime)
        TTL = int(config.read_config("Clients", "RequestTTL", "30"))

        if Delta > TTL:
            logging.getLogger(__name__).warning("Send package is already max age!")
            return ReturnError

        # client secret
        SecKey = SecMsgBytes.decode("utf-8")
        # function to call
        SecFunc = SecFuncBytes.decode("utf-8")
        logging.getLogger(__name__).debug("Client requested method: %s", SecFunc)

        ReturnSuccess = DecryptedMessage(
            ReturnCode.CLIENT_AUTH, SecKey, SecFunc, PKClient
        )

        return ReturnSuccess

    # no PK that is stored could decode the message
    logging.getLogger(__name__).warning(
        "Sent message could not be decrypted with any key!"
    )
    return ReturnError


def encrypt_message(PKClient: PublicKey, Message: str) -> str:
    """Encrypts a message string. Returns as safe base64 encoded string"""
    MsgBox = Box(__SKStore[0], PKClient)
    SecMsgBytes = Message.encode("utf-8")
    MsgEncrypt = MsgBox.encrypt(SecMsgBytes)

    StrMsg = base64.urlsafe_b64encode(MsgEncrypt).decode("utf-8")

    return StrMsg
