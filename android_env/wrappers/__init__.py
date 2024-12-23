# coding=utf-8
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
# Revised by Danyang Zhang @X-Lance based on
# 
# Copyright 2021 DeepMind Technologies Limited.
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

"""Init file for android_env.wrappers package."""

from android_env.wrappers import discrete_action_wrapper
from android_env.wrappers import flat_interface_wrapper
from android_env.wrappers import float_pixels_wrapper
from android_env.wrappers import image_rescale_wrapper
from android_env.wrappers import last_action_wrapper
from android_env.wrappers import vh_io_wrapper
from android_env.wrappers import recorder_wrapper
from android_env.wrappers import tap_action_wrapper

#from absl import logging
#import logging
import warnings

#logger = logging.getLogger("mobile_env.wrapper")

DiscreteActionWrapper = discrete_action_wrapper.DiscreteActionWrapper
FlatInterfaceWrapper = flat_interface_wrapper.FlatInterfaceWrapper
FloatPixelsWrapper = float_pixels_wrapper.FloatPixelsWrapper
ImageRescaleWrapper = image_rescale_wrapper.ImageRescaleWrapper
LastActionWrapper = last_action_wrapper.LastActionWrapper
VhIoWrapper = vh_io_wrapper.VhIoWrapper
TapActionWrapper = tap_action_wrapper.TapActionWrapper
RecorderWrapper = recorder_wrapper.RecorderWrapper

try:
    from android_env.wrappers import gym_wrapper
    GymInterfaceWrapper = gym_wrapper.GymInterfaceWrapper
except ModuleNotFoundError:
    #logger.warning("Gymnasium is not found. `pip install gymnasium` to enable GymInterfaceWrapper.")
    warnings.warn( "Gymnasium is not found. `pip install gymnasium` to enable GymInterfaceWrapper."
                 , ImportWarning
                 )

try:
    from android_env.wrappers import dmenv_wrapper
    DMEnvInterfaceWrapper = dmenv_wrapper.DMEnvInterfaceWrapper
except ModuleNotFoundError:
    #logger.warning("DM-Env is not found. `pip install dm-env` to enable DMEnvInterfaceWrapper.")
    warnings.warn( "DM-Env is not found. `pip install dm-env` to enable DMEnvInterfaceWrapper."
                 , ImportWarning
                 )
