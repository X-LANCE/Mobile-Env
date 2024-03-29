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

# NOTE: frida-server seems not to work on amd64 Android images in container. I
# have to leave it on the shelf temporarily.
#
# Related issue: https://github.com/remote-android/redroid-doc/issues/286

# zdy023/mobile-env-rl:v2.1.a30_ga.frida.f14.2.2.part

FROM zdy023/mobile-env-rl:v2.1.a30_ga.base

WORKDIR /root

COPY ./frida-server-14.2.2-android-x86_64.xz ./frida_setup.sh ./setup_image.sh ./
