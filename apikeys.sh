#!/bin/bash

set_env_var() {
    local var_name=$1
    read -r -p "$var_name >>> " var_value
    export "$var_name=$var_value"
}


set_env_var "CLIENT_ID"
set_env_var "CLIENT_SECRET"
