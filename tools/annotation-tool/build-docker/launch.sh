#!/bin/bash

export WIKIHOW_SERVER=${1-127.0.0.1}
export WIKIHOW_PORT=${2-8081}
annotator_name=${3-"Annotator Anonym"}
shift 3

replay_hosts=""
for h in "$@"; do
    replay_hosts=$replay_hosts"--set replay_host=$h "
done

mitmdump --showhost --ssl-insecure --set upstream_cert=false -s mitmscripts/replay_url2_local.py $replay_hosts &>>/dev/null &

cd backend
python server.py "/data/dump/$annotator_name.pkl" /data/task_path/tasks

kill %1
