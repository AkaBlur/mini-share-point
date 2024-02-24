from flask import Blueprint, request, jsonify
import logging
import time

from . import function_factory, sec_client, sec_server, config


Datapoint = Blueprint("data", __name__, url_prefix="/data")
IPTable: dict[str, int] = {}


def check_request_ip(IPAddress: str):
    MaxTTL = int(config.read_config("Server", "IPAddressTTL", "300"))

    if IPAddress not in IPTable:
        IPTable[IPAddress] = int(time.time())
        logging.getLogger(__name__).warning("New request from IP: %s", IPAddress)

    else:
        LastReq = IPTable[IPAddress]

        # IP with last request is too old
        if abs(LastReq - int(time.time())) > MaxTTL:
            logging.getLogger(__name__).warning(
                "Remote address with a new connection! IP: %s", IPAddress
            )

        # always set new timestamp
        IPTable[IPAddress] = int(time.time())

    Time = int(time.time())
    for IP in IPTable:
        IPTime = IPTable[IP]

        # scrap IP entry if over the max TTL
        if abs(IPTime - Time) > MaxTTL:
            IPTable.pop(IP, "")


@Datapoint.route("/", methods=["POST"])
def post_data_json():
    PostJson = request.get_json(silent=True)

    if PostJson is None:
        logging.getLogger(__name__).info("Malformed JSON from: %s", request.remote_addr)
        return "", 401

    if (
        "id" in PostJson
        and "check" in PostJson
        and "ts" in PostJson
        and "entry" in PostJson
    ):
        IDSent = PostJson["id"]
        CRCSent = PostJson["check"]
        TimeSent = PostJson["ts"]
        FuncSent = PostJson["entry"]
        DecryptResponse: sec_server.DecryptedMessage = sec_server.decrypt_remote_call(
            IDSent, CRCSent, TimeSent, FuncSent
        )

        # message could not be decrypted -> no key registered
        if DecryptResponse.ReturnCode == sec_server.ReturnCode.NOT_AUTHORIZED:
            logging.getLogger(__name__).info(
                "Unauthorized endpoint tried connecting - %s", request.remote_addr
            )
            return "", 401

        Registered = sec_client.check_client_register(DecryptResponse.ClientSecret)

        if Registered:
            FunctionVal = function_factory.call_module(DecryptResponse.FunctionCall)
            ResponseEncrypt = sec_server.encrypt_message(
                DecryptResponse.ClientKey, FunctionVal
            )

            check_request_ip(request.remote_addr)

            return jsonify(value=ResponseEncrypt), 200

        else:
            logging.getLogger(__name__).warning(
                "Key Error on decrypted message! %s sent unregistered SECRET! Client Private Key may be compromised!",
                request.remote_addr,
            )
            return "", 401

    logging.getLogger(__name__).info("Malformed request from: %s", request.remote_addr)
    return "", 401
