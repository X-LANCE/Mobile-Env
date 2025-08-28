# Copyright 2025 SJTU X-Lance Lab
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

# zdy023/mobile-env:$mobtag-ubuntu20.04-cu121-android30-torch241
FROM nvidia/cuda:12.1.0-runtime-ubuntu20.04 AS mobile-env

WORKDIR /root

COPY ./commandlinetools-linux-latest.zip ./android-package.list ./install_sdk.exp ./install_python.exp ./

RUN apt update -y &&\
	apt install -y openjdk-17-jre expect unzip vim less &&\
	./install_python.exp

ENV ANDROID_HOME="/root/Android/Sdk"
#ENV AVD_NAME="Pixel_2_API_30_ga_x64"
ENV PATH=$ANDROID_HOME/cmdline-tools/bin:$PATH
ENV PATH=$ANDROID_HOME/emulator:$PATH
ENV PATH=$ANDROID_HOME/platform-tools:$PATH

#include proxy.dockerfile

RUN mkdir -p $ANDROID_HOME &&\
    unzip commandlinetools-linux-latest.zip -d $ANDROID_HOME &&\
	./install_sdk.exp

#COPY ./android_env/ ./mobile-env/
RUN --mount=type=cache,target=/root/.cache/pip\
	--mount=type=bind,target=/root/mobile-env,source=./android_env,rw\
	pip install -i https://mirrors.bfsu.edu.cn/pypi/web/simple --upgrade pip &&\
	pip install -i https://mirrors.bfsu.edu.cn/pypi/web/simple torch==2.4.1 torchvision==0.19.1 networkx==3.1 --extra-index-url https://download.pytorch.org/whl/cu121 &&\
	cd ./mobile-env && pip install -i https://mirrors.bfsu.edu.cn/pypi/web/simple -e ".[easyocr,gym,dmenv]"
VOLUME /root/mobile-env

#COPY ./requirements-instruction_rewriting.txt ./
#RUN --mount=type=cache,target=/root/.cache/pip\
	#pip install -i https://mirrors.bfsu.edu.cn/pypi/web/simple -r requirements-instruction_rewriting.txt &&\
	#python -m nltk.downloader popular &&\
	#pip install -i https://mirrors.bfsu.edu.cn/pypi/web/simple pillow

VOLUME /root/.android

#RUN avdmanager create avd -n $AVD_NAME -c 8G -k "system-images;android-30;google_apis;x86_64" -d pixel_2 &&\
	#cd ~/.android/avd/$AVD_NAME.avd/ &&\
	#sed -i.bak -e 's#^\(image\.sysdir\.1[[:space:]]*=[[:space:]]*\)Sdk/#\1#g' config.ini

ENV ADB_MDNS=0
