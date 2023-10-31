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

# zdy023/mobile-env-rl:v2.1.a30_ga.syscert.m8.0.0.part

FROM zdy023/mobile-env-rl:v2.1.a30_ga.base

WORKDIR /root

COPY ./syscert_setup.exp ./setup_image.sh ./

RUN pip install mitmproxy==8.0.0 Werkzeug==2.2.2 &&\
	pip install --upgrade protobuf

# /root/mitmscripts/replay.py will be used as replay script
#VOLUME /root/mitmscripts
