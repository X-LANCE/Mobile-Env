# Copyright 2024 SJTU X-Lance Lab
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
# 
# Created by Danyang Zhang @X-Lance

import abc
import .timestep
import .spec

class Environment(abc.ABC):
    @abc.abstractmethod
    def switch_task(self, index: int) -> timestep.TimeStep:
        raise NotImplementedError()

    @abc.abstractmethod
    def reset(self) -> timestep.TimeStep:
        raise NotImplementedError()

    @abc.abstractmethod
    def step(self, action: Any) -> timestep.TimeStep:
        raise NotImplementedError()

    @abc.abstractmethod
    def observation_spec(self) -> spec.Array:
        raise NotImplementedError

    @abc.abstractmethod
    def action_spec(self) -> spec.Array:
        raise NotImplementedError

    @abc.abstractmethod
    def command(self) -> 
