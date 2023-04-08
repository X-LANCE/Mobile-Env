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

.PHONY: backend docker1 docker2 rmi1 rmi2
backend:
	rm -rf backend/template/ backend/static/
	rsync -ruvt --exclude=index.html frontend/dist/ backend/static/
	rsync -ruvt frontend/dist/index.html backend/template/

docker_dir := build-docker
#image_tag := my/android-env-web:0.4 # ready image
#image_tag1 := my/android-env-web:0.5 # manual setup
#image_tag := my/android-env-web:0.7 # manual setup final
#image_tag := my/android-env-web:0.8 # manual setup
#image_tag := my/android-env-web:0.9 # ready image 2

image_tag1 := my/android-env-web:0.5
image_tag2 := my/android-env-web:2.0m1.1a.h1.0

docker1:
	#mkdir $(docker_dir)/android_env
	rsync -ruvth --progress --exclude=__pycache__ ../android_env/android_env ../android_env/setup.py $(docker_dir)/android_env/
	rsync -ruvth --progress ../android_env/tools/syscert_setup.exp $(docker_dir)/
	rsync -ruvth --progress --exclude=__pycache__ --exclude="*.pkl" --exclude=tags backend/ $(docker_dir)/backend/
	rsync -ruvth --progress ../android_env/apps/wikihow/mitmscripts/replay_url2_local.py $(docker_dir)/mitmscripts/
	docker build --tag $(image_tag1) --file $(docker_dir)/Dockerfile1 $(docker_dir)/

docker2:
	docker build --tag $(image_tag2) --file $(docker_dir)/Dockerfile2 $(docker_dir)/

rmi1:
	docker ps -a --filter "ancestor=$(image_tag1)" |awk '{if(NR>=2) {system("docker rm "$$1);}}'
	docker rmi $(image_tag1)
	docker images

rmi2:
	docker ps -a --filter "ancestor=$(image_tag2)" |awk '{if(NR>=2) {system("docker rm "$$1);}}'
	docker rmi $(image_tag2)
	docker images
