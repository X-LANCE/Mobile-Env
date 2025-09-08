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

.PHONY: mobile-env docker-test-dir

docker_dir := build-docker

mobile_env_path := $(docker_dir)/android_env
mobile_env_commit_dig := $(shell cd $(mobile_env_path) && git log --oneline HEAD^..HEAD |cut -d' ' -f 1)
mobenv_tag := zdy023/mobile-env:$(mobile_env_commit_dig)-ubuntu20.04-cu121-android30-torch241

mobile-env: $(docker_dir)/real.dockerfile
	rsync -ruvth --delete --exclude=__pycache__ android_env setup.py pyproject.toml LICENSE $(docker_dir)/android_env/
	docker buildx build -f $< --target $@ -t $(mobenv_tag) $(docker_dir)/

$(docker_dir)/real.dockerfile: $(docker_dir)/Dockerfile $(docker_dir)/proxy.dockerfile
	zpp -m C $< -o $@

docker-test-dir:
	mkdir -p docker_tests
	rsync -ruvth --delete --exclude=__pycache__ android_env setup.py pyproject.toml LICENSE docker_tests/mobile-env/
	mkdir -p docker_tests/android_avds
