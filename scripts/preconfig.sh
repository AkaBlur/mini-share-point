#!/bin/bash
# preconfiguration script for internal docker usage

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