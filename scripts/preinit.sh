#!/bin/bash
# preinitialization script that sets up necessary files if not provided

# INI - CONFIG FILES
# initial configuration file
if [ ! -e "$MSP_CONFIG_PATH" ];then
    cp "/defaults/config/config.ini" "$MSP_CONFIG_PATH"
    chmod 644 "$MSP_CONFIG_PATH"
fi
# initial module configuration file
if [ ! -e "$MSP_MODCONF_PATH" ];then
    cp "/defaults/config/modules.ini" "$MSP_MODCONF_PATH"
    chmod 644 "$MSP_MODCONF_PATH"
fi

# MODULES
MOD_INIT_FILE=/app/modules/__init__.py
MOD_REQ_FILE=/app/modules/module-requirements.txt
MOD_TUT_FILE=/app/modules/simple_time.py
if [ ! -e "$MOD_REQ_FILE" ];then
    cp "/defaults/modules/module-requirements.txt" "$MOD_REQ_FILE"
    chmod 644 "$MOD_REQ_FILE"
fi
if [ ! -e "$MOD_INIT_FILE" ];then
    cp "/defaults/modules/__init__.py" "$MOD_INIT_FILE"
    chmod 644 "$MOD_INIT_FILE"
fi
if [ ! -e "$MOD_TUT_FILE" ];then
    cp "/defaults/modules/simple_time.py" "$MOD_TUT_FILE"
    chmod 644 "$MOD_TUT_FILE"
fi

# create empty client secret file
CLIENTDEV="/sec/clients.dev"
SECDIR="/sec"
LOGDIR="/log"

if [ ! -d "$LOGDIR" ];then
    mkdir -m 777 "$LOGDIR"
fi

chmod -R 777 "$LOGDIR"

if [ ! -d "$SECDIR" ];then
    mkdir -m 755 "$SECDIR"
fi

# keys inside sec should always be readable by the server
chmod -R 644 "$SECDIR"
# needed for cd access
chmod 755 "$SECDIR"

if [ ! -e "$CLIENTDEV" ];then
    touch "$CLIENTDEV"
    chmod 644 "$CLIENTDEV"
fi

# check and create server keyfiles
if [ ! -e "/sec/server.key" -a ! -e "/sec/server.pub" ];then
    python3 /app/util/gen_key.py pair /sec/server
    chmod 644 /sec/server.key
    chmod 644 /sec/server.pub
fi

# install module requirements if supplied
if [ -s "$MOD_REQ_FILE" ];then
    pip install -r "$MOD_REQ_FILE"
fi