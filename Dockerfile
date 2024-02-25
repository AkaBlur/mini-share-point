FROM python:3.11.8-slim-bookworm

# environment variables for shipping
ENV MSP_LOGLEVEL=INFO
ENV MSP_MAXLOGS=5
ENV MSP_CONFIG_PATH=/config/config.ini
ENV MSP_MODCONF_PATH=/config/modules.ini
ENV MSP_LOGFILE_PATH=/log

# SETUP
# configuration
COPY --chmod=644 config-docker /config/
# custom modules
COPY --chmod=644 modules /app/modules/

# Python packages
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Utility stuff
COPY --chmod=644 util /app/util/

# Run preconfigure setup script for internal docker setup
COPY --chmod=700 scripts/preconfig.sh /app/preconfig.sh

# script for append clients to the local storage
COPY --chmod=700 scripts/appendclient /usr/bin/appendclient
# script for deleting all clients
COPY --chmod=700 scripts/purgeclients /usr/bin/purgeclients

# Entrypoint
COPY --chmod=700 scripts/bootstrap.sh /app/bootstrap.sh

# Codebase
COPY --chmod=644 mini_share_point /app/mini_share_point/
WORKDIR /app

# USER SECTION
ENTRYPOINT [ "./bootstrap.sh" ]