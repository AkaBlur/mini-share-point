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