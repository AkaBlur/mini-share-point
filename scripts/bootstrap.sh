#!/bin/bash
# initialization script for starting up server

# running preinit, if mounted dirs are empty
./preinit.sh
# running preconfiguration for setup
./preconfig.sh

# check and update user UID and GID for default user
if [ -z "${PUID-}" ];then
    export PUID=1000
fi

if [ -z "${PGID-}" ];then
    export PGID=100
fi

# check if container is at first startup
# saves them for next usage
if [ ! -f "/root/puid" ] && [ ! -f "/root/pgid" ]; then
    # USER and GROUP creation process
    # check if the group ID is free or 100 for the users default otherwise fail
    # users group will be the default group
    if [ -z "$(cat /etc/group | grep ":$PGID:")" ] || [[ "$PGID" == "100" ]]; then
        groupmod -g $PGID users

    else
        echo "Group $PGID already exists! Choose non-default one."
        exit 1

    fi

    # check if a non-default user ID is given
    if [ -z "$(cat /etc/passwd | grep ":$PUID:")" ]; then
        useradd msppython -u $PUID -g $PGID -m -s /bin/bash

    else
        echo "Given UID $PUID already exists! Choose non-default one."
        exit 1

    fi

    echo "$PUID" > /root/puid
    echo "$PGID" > /root/pgid

else
    if [ ! "$PUID" == "$(cat /root/puid)" ] || [ ! "$PGID" == "$(cat /root/pgid)" ]; then
        echo "UID/GID changed from last startup!"
        echo "This is not possible. Build the image with the correct UID/GID in the first place!"
        exit 1
        
    fi

fi

# custom module location
if [ -z "${PYTHONPATH-}" ];then
    export PYTHONPATH=/app/modules
fi

# run server as msppython user
su -c 'gunicorn -b 0.0.0.0:8000 "mini_share_point:create_app()"' msppython