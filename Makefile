#!/usr/bin/make -f
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

.PHONY: base syscert frida rmiB rmiS rmiF

docker_dir := build-docker

itag_base := zdy023/mobile-env-rl:v2.1.a30_ga.base
itag_syscert := zdy023/mobile-env-rl:v2.1.a30_ga.syscert.m8.0.0.part
itag_syscert_full := zdy023/mobile-env-rl:v2.1.a30_ga.syscert.m8.0.0
itag_frida := zdy023/mobile-env-rl:v2.1.a30_ga.frida.f14.2.2.part
itag_frida_full := zdy023/mobile-env-rl:v2.1.a30_ga.frida.f14.2.2

base:
	rsync -ruvth --delete --exclude=__pycache__ android_env setup.py pyproject.toml LICENSE $(docker_dir)/android_env/
	docker build --tag $(itag_base) --file $(docker_dir)/base.dockerfile $(docker_dir)/
	
syscert:
	rsync -ruvth --delete tools/syscert_setup.exp $(docker_dir)/
	docker build --tag $(itag_syscert) --file $(docker_dir)/syscert.dockerfile $(docker_dir)/

frida:
	rsync -ruvth --delete tools/frida_setup.sh $(docker_dir)/
	docker build --tag $(itag_frida) --file $(docker_dir)/frida.dockerfile $(docker_dir)/

rmiB:
	docker ps -a --filter "ancestor=$(itag_base)" |awk '{if(NR>=2) {system("docker rm "$$1);}}'
	docker rmi $(itag_base)
	docker images

rmiS:
	docker ps -a --filter "ancestor=$(itag_syscert)" |awk '{if(NR>=2) {system("docker rm "$$1);}}'
	docker rmi $(itag_syscert)
	docker ps -a --filter "ancestor=$(itag_syscert_full)" |awk '{if(NR>=2) {system("docker rm "$$1);}}'
	docker rmi $(itag_syscert_full)
	docker images

rmiF:
	docker ps -a --filter "ancestor=$(itag_frida)" |awk '{if(NR>=2) {system("docker rm "$$1);}}'
	docker rmi $(itag_frida)
	docker ps -a --filter "ancestor=$(itag_frida_full)" |awk '{if(NR>=2) {system("docker rm "$$1);}}'
	docker rmi $(itag_frida_full)
	docker images
