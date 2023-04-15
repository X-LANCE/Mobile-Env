#!/bin/bash
# Copyright 2023 SJTU X-Lance Lab
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Created by Danyang Zhang @X-Lance.

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
