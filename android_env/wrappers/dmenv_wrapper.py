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
# 
# Created by Danyang Zhang @X-Lance

from android_env.wrappers.base_wrapper import BaseWrapper
import dm_env
from android_env.interfaces.env import Environment
from android_env import interfaces
from android_env.interfaces.timestep import TimeStep
from typing import Dict, List
from typing import Union

class DMEnvInterfaceWrapper(BaseWrapper, dm_env.Environment):
    def __init__(self, env: Environment):
        super(DMEnvInterfaceWrapper, self).__init__(env)

    def _convert_spec( self
                     , spec: Union[ List[interfaces.specs.Array]
                                  , Dict[str, interfaces.specs.Array]
                                  , interfaces.specs.Array
                                  ]
                     ) -> Union[ List[dm_env.specs.Array]
                               , Dict[str, dm_env.specs.Array]
                               , dm_env.specs.Array
                               ]:
        if isinstance(spec, list):
            return [self._convert_spec(sp) for sp in spec]
        if isinstance(spec, dict):
            return {n: self._convert_spec(sp) for n, sp in spec.items()}
        if isinstance(spec, interfaces.specs.DiscreteArray):
            return dm_env.specs.DiscreteArray( spec.num_values
                                             , spec.dtype
                                             , spec.name
                                             )
        if isinstance(spec, interfaces.specs.BoundedArray):
            return dm_env.specs.BoundedArray( spec.shape
                                            , spec.dtype
                                            , spec.minimum
                                            , spec.maximum
                                            , spec.name
                                            )
        if isinstance(spec, interfaces.specs.StringArray):
            return dm_env.specs.StringArray( spec.shape
                                           , spec.string_type
                                           , spec.name
                                           )
        if isinstance(spec, interfaces.specs.Array):
            return dm_env.specs.Array( spec.shape
                                     , spec.dtype
                                     , spec.name
                                     )

    def observation_spec(self) -> dm_env.specs.Array:
        return self._convert_spec(self.observation_spec())
    def action_spec(self) -> dm_env.specs.Array:
        return self._convert_spec(self.action_spec())

    def _process_timestep(self, timestep: TimeStep) -> dm_env.TimeStep:
        return dm_env.TimeStep( step_type=dm_env.StepType(timestep.step_type)
                              , reward=timestep.reward
                              , discount=1.
                              , observation=timestep.observation
                              )
