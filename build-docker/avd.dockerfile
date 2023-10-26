# zdy023/avd

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

# configure python environment
COPY ./android-env-web-small.txt ./
COPY ./android_env/ ./android_env/
COPY ./backend/ ./backend/
COPY ./mitmscripts/ ./mitmscripts/
RUN pip config set global.index-url https://mirrors.bfsu.edu.cn/pypi/web/simple &&\
	pip install --upgrade pip && \
    pip install -r android-env-web-small.txt &&\
    pip install --upgrade protobuf &&\
    cd android_env && pip install .

COPY ./syscert_setup.exp ./setup_image.sh ./
