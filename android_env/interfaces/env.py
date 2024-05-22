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
from . import timestep
from . import spec
from typing import Any, Union
from typing import List

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
        raise NotImplementedError()

    @abc.abstractmethod
    def action_spec(self) -> spec.Array:
        raise NotImplementedError()

    def command(self) -> List[str]:
        return []

    def vocabulary(self) -> List[str]:
        return []

    @property
    def nb_tasks(self) -> int:
        return 0

    @property
    def task_index(self) -> int:
        return 0

    @property
    def task_id(self) -> str:
        return ""

    @property
    def task_name(self) -> str:
        return 0

    @property
    def task_description(self) -> str:
        return ""

    @abc.abstractmethod
    def task_instructions(self, latest_only: bool = False) -> Union[str, List[str]]:
        raise NotImplementedError()

    @abc.abstractclassmethod
    def task_extras(self, latest_only: bool = True) -> Dict[str, np.ndarray]:
        raise NotImplementedError()

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError()
