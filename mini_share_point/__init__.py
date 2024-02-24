from flask import Flask
import logging
import logging.handlers
import os
from werkzeug.middleware.proxy_fix import ProxyFix

from . import config, data, function_factory, sec_client, sec_server

__logLevel = os.getenv("MSP_LOGLEVEL", "INFO")
__maxLogs = int(os.getenv("MSP_MAXLOGS", "5"))
__configPath = os.getenv("MSP_CONFIG_PATH", "config/config.ini")
__moduleConfig = os.getenv("MSP_MODCONF_PATH", "config/modules.ini")
__logPath = os.getenv("MSP_LOGFILE_PATH", "log")


def setup_server(instance: Flask) -> bool:
    """Basic setup for all server functions"""
    logging.getLogger(__name__).debug("Configuring server")
    # load all module extensions for the server to use
    if not function_factory.load_mods(__moduleConfig):
        logging.getLogger(__name__).critical("Could not setup module extensions!")
        return False

    # registering data endpoint
    instance.register_blueprint(data.Datapoint)

    # loading client secrets
    if not sec_client.load_client_secret(
        config.read_config("Clients", "Register", "sec/clients.dev")
    ):
        return False

    # load client public keys
    sec_client.load_client_keys(config.read_config("Clients", "Keypath", "sec"))

    # load server private key
    if not sec_server.load_server_key(config.read_config("Server", "Keypath", "sec")):
        return False

    # Proxy headers; sets number of:
    # X-Forwarded-For
    # X-Forwarded-Host
    # X-Forwarded-Port
    # X-Forwarded-Prefix
    # X-Forwarded-Proto
    instance.wsgi_app = ProxyFix(
        instance.wsgi_app,
        x_for=int(config.read_config("Proxy", "ForwardFor", "0")),
        x_host=int(config.read_config("Proxy", "ForwardHost", "0")),
        x_port=int(config.read_config("Proxy", "ForwardPort", "0")),
        x_prefix=int(config.read_config("Proxy", "ForwardPrefix", "0")),
        x_proto=int(config.read_config("Proxy", "ForwardProto", "0")),
    )

    logging.getLogger(__name__).debug("Configuration of server done")
    return True


def create_app():
    # logging setup
    logLevel: int

    if __logLevel.upper() == "DEBUG":
        logLevel = logging.DEBUG

    elif __logLevel.upper() == "INFO":
        logLevel = logging.INFO

    elif __logLevel.upper() == "WARNING":
        logLevel = logging.WARNING

    elif __logLevel.upper() == "ERROR":
        logLevel = logging.ERROR

    elif __logLevel.upper() == "CRITICAL":
        logLevel = logging.CRITICAL

    else:
        logLevel = logging.WARNING

    LogFileHandler = logging.handlers.RotatingFileHandler(
        (__logPath + "/latest.log"),
        maxBytes=(1024 * 1024 * 10),
        backupCount=__maxLogs,
        encoding="utf-8",
    )
    logging.basicConfig(
        format="[%(asctime)s][MINI-SEC-POINT] %(levelname)s in %(filename)s: %(message)s",
        handlers=[LogFileHandler, logging.StreamHandler()],
    )

    App = Flask(__name__)
    App.logger.info("Starting up mini-share-point!")
    App.logger.setLevel(logLevel)
    logging.getLogger(__name__).debug("Log setup complete")

    # configuration init
    logging.getLogger(__name__).debug("Loading config file")
    if not config.load_config(__configPath):
        logging.getLogger(__name__).critical("Configuration setup error!")
        exit(1)

    # setup server
    if not setup_server(App):
        logging.getLogger(__name__).critical("Server setup error!")
        exit(1)

    return App
