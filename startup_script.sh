#!/bin/bash

sigint_handler() {
    true
}

trap sigint_handler SIGINT

clear

basedir="/srv/planthealth"
config_yaml_path="${basedir}/conf.yaml"
python_path="${basedir}/main.py"
config_path="${basedir}/configure"

if [ -f "$config_yaml_path" ]; then
    echo "conf.yaml exists, running Python script."
    /usr/bin/python3 "$python_path"
else
    ( echo "conf.yaml not found, running configure script first."
    /bin/bash "$config_path" ) &&

    ( echo "conf.yaml created, running python script now."
    /usr/bin/python3 "$python_path" ) ||

    ( echo "Configure script aborted, dropping to shell."
    /usr/bin/sudo -u pi /bin/bash )
fi
