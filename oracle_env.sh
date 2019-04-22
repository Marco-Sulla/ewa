#!/usr/bin/env sh

# change it with the version of the oracle client
oracle_ver="18.5"
export ORACLE_HOME="/usr/lib/oracle/$oracle_ver/client64"
export PATH="$PATH:$ORACLE_HOME/bin"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$ORACLE_HOME/lib"

