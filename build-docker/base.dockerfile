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

# zdy023/mobile-env-rl:v2.1.a30_ga.base

FROM pytorch/pytorch:1.12.0-cuda11.3-cudnn8-runtime

WORKDIR /root

# install JRE and expect
RUN apt update -y &&\
    apt install -y openjdk-17-jre expect

ENV ANDROID_HOME="/root/Android/Sdk"
ENV AVD_NAME="Pixel_2_API_30_ga_x64"

# install android emulator
COPY ./commandlinetools-linux-latest.zip ./android-package.list ./install_sdk.exp ./
RUN mkdir -p $ANDROID_HOME &&\
    unzip commandlinetools-linux-latest.zip -d $ANDROID_HOME &&\
    ./install_sdk.exp &&\
    echo 'export PATH='$ANDROID_HOME'/cmdline-tools/bin:$PATH' >>/root/.bashrc &&\
    echo 'export PATH='$ANDROID_HOME'/emulator:$PATH' >>/root/.bashrc &&\
    echo 'export PATH='$ANDROID_HOME'/platform-tools:$PATH' >>/root/.bashrc

COPY ./android_env/ ./android_env/
#RUN pip config set global.index-url https://mirrors.bfsu.edu.cn/pypi/web/simple &&\
RUN pip install --upgrade pip &&\
	cd android_env && pip install .
