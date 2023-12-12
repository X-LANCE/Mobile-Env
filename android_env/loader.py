# coding=utf-8
# vim: set tabstop=2 shiftwidth=2:
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

"""Function for loading AndroidEnv."""

import os
import os.path

from android_env import environment
from android_env.components import coordinator as coordinator_lib
from android_env.components import task_manager as task_manager_lib
from android_env.components.simulators.emulator import emulator_simulator
from android_env.components.simulators.remote import remote_simulator
from android_env.proto import task_pb2
from android_env.components.tools.types import TextModel, IconModel
from android_env.components.tools import naive_functions
from android_env.components.tools.sbert_holder import SBERTHolder
from android_env.utils import fix_path

from google.protobuf import text_format

from typing import Optional, Any
from typing import Dict, Tuple
import functools

def load( task_path: str
        , avd_name: str
        , android_avd_home: str = '~/.android/avd'
        , android_sdk_root: str = '~/Android/Sdk'
        , emulator_path: str = '~/Android/Sdk/emulator/emulator'
        , adb_path: str = '~/Android/Sdk/platform-tools/adb'
        , run_headless: bool = False
        , mitm_config: Optional[Dict[str, str]] = None
        , start_token_mark: str = ""
        , non_start_token_mark: str = "##"
        , special_token_pattern: str = r"\[\w+\]"
        , unify_vocabulary: Optional[str] = None
        , text_model: TextModel = naive_functions
        , icon_model: IconModel = naive_functions
        , sbert_holder: Optional[SBERTHolder] = None
        , with_view_hierarchy: bool = False
        , coordinator_args: Optional[Dict[str, Any]] = None
        ) -> environment.AndroidEnv:
  """Loads an AndroidEnv instance.

  Args:
    task_path: Path to the task textproto file or the directory of task
      textproto file set
    avd_name: Name of the AVD (Android Virtual Device).

    android_avd_home: Path to the AVD (Android Virtual Device).
    android_sdk_root: Root directory of the SDK.
    emulator_path: Path to the emulator binary.
    adb_path: Path to the ADB (Android Debug Bridge).
    run_headless: If True, the emulator display is turned off.
    mitm_config: An optional dict to config the launch options if an mitm proxy
      is in need for a web-based app. The dict is expected to have a struture
      like
        {
            "method": "syscert" | "frida" | "packpatch",
            "address": str as the address for the mitm proxy server, default to
              "127.0.0.1",
            "port": str as the port for the mitm proxy server, default to
              "8080",
            "frida-server": an option for method "frida", to indicate the path
              to the executable of frida-server on the android system, default
              to "/data/local/tmp/frida-server",
            "frida": an option for method "frida", to indicate the path to the
              executable of frida on the local machine, default to "frida",
            "frida-script": an option for method "frida", to indicate the
              script used to hijack the target applicationa, default to
              "frida-script.js",
            "patch-suffix": an option for method "packpatch", to indicate the
              suffix $suff with which the package name "$package.apk" to be
              installed is replaced to "$package-$suff.apk", default to
              "patched"
        }

    start_token_mark: str as the mark for the start subwords such as "Ġ"
      (\\u0120) for GPT subword
    non_start_token_mark: str as the mark for the non-start subwords such as
      "##" for BERT subword
    special_token_pattern: str as the pattern of the special non-printable
      tokens such as "[CLS]" for BERT tokens
    unify_vocabulary: str or none as a file name to the vocabulary file in
      which each line constitutes a token.

    text_model (TextModel): text model to conduct text recognition on the
      screen
    icon_model (IconModel): icon model to conduct icon recognition on the
      screen
    sbert_holder (Optional[SBERTHolder]): an optional customer SBERT holder

    with_view_hierarchy (bool): if the view hierarchy should be included in the
      observation

    coordinator_args (Optional[Dict[str, Any]]): overrides several default
      arguments of Coordinator

  Returns:
    env: An AndroidEnv instance.
  """

  adb_controller_args = dict(
      adb_path=os.path.expanduser(adb_path),
      adb_server_port=5037,
      prompt_regex=r'\w*:\/ [$#]')
  emulator_launcher_args = dict(
      avd_name=avd_name,
      android_avd_home=os.path.expanduser(android_avd_home),
      android_sdk_root=os.path.expanduser(android_sdk_root),
      emulator_path=os.path.expanduser(emulator_path),
      run_headless=run_headless,
      gpu_mode='swiftshader_indirect',
      writable_system=False)
  coordinator_args: Dict[str, Any] = coordinator_args or {}

  # Prepare task.
  task_list = []
  if os.path.isdir(task_path):
    task_paths = list( map( functools.partial(os.path.join, task_path)
                          , sorted(
                              filter( lambda f: f.endswith(".textproto")
                                    , os.listdir(task_path)
                                    )
                              )
                          )
                     )
    task_directory = task_path
  else:
    task_paths = [task_path]
    task_directory = os.path.dirname(task_path)
  for t_p in task_paths:
    task = task_pb2.Task()
    with open(t_p, 'r') as proto_file:
      text_format.Parse(proto_file.read(), task)
    task_list.append(task)

  adb_root = False
  frida_server = None
  if mitm_config is not None:
    emulator_launcher_args["writable_system"] = True
    emulator_launcher_args["proxy_address"] = mitm_config.get("address", "127.0.0.1")
    emulator_launcher_args["proxy_port"] = mitm_config.get("port", "8080")

    if mitm_config["method"]=="frida":
      adb_root = True
      frida_server = mitm_config.get("frida-server",
          "/data/local/tmp/frida-server")
      adb_controller_args["frida"] = mitm_config.get("frida", "frida")
      adb_controller_args["frida_script"] = mitm_config.get("frida-script",
          "frida-script.js")
    elif mitm_config["method"]=="packpatch":
      for t in task_list:
        for st in t.setup_steps:
          if st.HasField("adb_call") and\
              st.adb_call.HasField("install_apk"):
            apk_path = st.adb_call.install_apk.filesystem.path
            main_name, extension = os.path.splitext(apk_path)
            st.adb_call.install_apk.filesystem.path =\
                "{:}-{:}{:}".format(main_name,
                  mitm_config.get("patch-suffix", "patched"),
                  extension)
    #elif mitm_config["method"]=="syscert":
      #adb_root = True

  # transform the paths in task definitions
  for t in task_list:
    #for st in t.setup_steps:
      #if st.HasField("adb_call") and\
          #st.adb_call.HasField("install_apk"):
        #apk_path = st.adb_call.install_apk.filesystem.path
        #if not os.path.isabs(apk_path):
          #st.adb_call.install_apk.filesystem.path =\
              #os.path.normpath(os.path.join(task_directory, apk_path))
    fix_path(t, task_directory)

  # Create simulator.
  #print("ZDY: BEFORE Simulator Initialization")
  simulator = emulator_simulator.EmulatorSimulator(
      adb_controller_args=adb_controller_args,
      emulator_launcher_args=emulator_launcher_args,
      adb_root=adb_root,
      frida_server=frida_server)
  #print("ZDY: AFTER Simulator Initialization")

  if unify_vocabulary is not None:
    with open(unify_vocabulary) as f:
      vocabulary = list(map(str.strip, f))
  else:
    vocabulary = None

  task_managers = list( map( functools.partial( task_manager_lib.TaskManager
                                              , start_token_mark=start_token_mark
                                              , non_start_token_mark=non_start_token_mark
                                              , special_token_pattern=special_token_pattern
                                              , fix_vocabulary_to=vocabulary
                                              , text_model=text_model
                                              , icon_model=icon_model
                                              , get_sbert=(sbert_holder or SBERTHolder()).get_sbert
                                              )
                           , task_list
                           )
                      )
  coordinator = coordinator_lib.Coordinator( simulator, task_managers
                                           , with_view_hierarchy=with_view_hierarchy
                                           , **coordinator_args
                                           )

  # Load environment.
  return environment.AndroidEnv(coordinator=coordinator)

def load_remote( task_path: str
               , address: str
               , port: int
               , timeout: float = 5.
               , launch_timeout: float = 2.
               , retry: int = 3
               , resize_for_transfer: Optional[Tuple[int, int]] = None
               , mitm_config: Optional[Dict[str, str]] = None
               , start_token_mark: str = ""
               , non_start_token_mark: str = "##"
               , special_token_pattern: str = r"\[\w+\]"
               , unify_vocabulary: Optional[str] = None
               , text_model: TextModel = naive_functions
               , icon_model: IconModel = naive_functions
               , sbert_holder: Optional[SBERTHolder] = None
               , with_view_hierarchy: bool = False
               , coordinator_args: Optional[Dict[str, Any]] = None
               ) -> environment.AndroidEnv:
  """Loads an AndroidEnv instance.

  Args:
    task_path (str): Path to the task textproto file or the directory of task
      textproto file set

    address (str): IP address of remote daemon
    port (int): listening port of remote daemone
    timeout (float): timeout for regular commands in secondes
    launch_timeout (float): timeout for commands `launch`, `start`, and
      `close` in **minutes**
    retry (int): retry times
    resize_for_transfer (Optional[Tuple[int, int]]): if the screen
      should be resized for transferring as (W, H)

    mitm_config: An optional dict to config the launch options if an mitm proxy
      is in need for a web-based app. The dict is expected to have a struture
      like
        {
            "method": "syscert" | "frida" | "packpatch",
            "address": str as the address for the mitm proxy server, default to
              "127.0.0.1",
            "port": str as the port for the mitm proxy server, default to
              "8080",
            "frida-server": an option for method "frida", to indicate the path
              to the executable of frida-server on the android system, default
              to "/data/local/tmp/frida-server",
            "frida": an option for method "frida", to indicate the path to the
              executable of frida on the local machine, default to "frida",
            "frida-script": an option for method "frida", to indicate the
              script used to hijack the target applicationa, default to
              "frida-script.js",
            "patch-suffix": an option for method "packpatch", to indicate the
              suffix $suff with which the package name "$package.apk" to be
              installed is replaced to "$package-$suff.apk", default to
              "patched"
        }

    start_token_mark (str): the mark for the start subwords such as "Ġ"
      (\\u0120) for GPT subword
    non_start_token_mark (str): the mark for the non-start subwords such as
      "##" for BERT subword
    special_token_pattern (str): the pattern of the special non-printable
      tokens such as "[CLS]" for BERT tokens
    unify_vocabulary (Optional[str]): a file name to the vocabulary file in
      which each line constitutes a token.

    text_model (TextModel): text model to conduct text recognition on the
      screen
    icon_model (IconModel): icon model to conduct icon recognition on the
      screen
    sbert_holder (Optional[SBERTHolder]): an optional customer SBERT holder

    with_view_hierarchy (bool): if the view hierarchy should be included in the
      observation

    coordinator_args (Optional[Dict[str, Any]]): overrides several default
      arguments of Coordinator

  Returns:
    env: An AndroidEnv instance.
  """

  coordinator_args: Dict[str, Any] = coordinator_args or {}

  # Prepare task.
  task_list = []
  if os.path.isdir(task_path):
    task_paths = list( map( functools.partial(os.path.join, task_path)
                          , sorted(
                              filter( lambda f: f.endswith(".textproto")
                                    , os.listdir(task_path)
                                    )
                              )
                          )
                     )
    task_directory = task_path
  else:
    task_paths = [task_path]
    task_directory = os.path.dirname(task_path)
  for t_p in task_paths:
    task = task_pb2.Task()
    with open(t_p, 'r') as proto_file:
      text_format.Parse(proto_file.read(), task)
    task_list.append(task)

  if mitm_config is not None and mitm_config["method"]=="packpatch":
    for t in task_list:
      for st in t.setup_steps:
        if st.HasField("adb_call") and\
            st.adb_call.HasField("install_apk"):
          apk_path = st.adb_call.install_apk.filesystem.path
          main_name, extension = os.path.splitext(apk_path)
          st.adb_call.install_apk.filesystem.path =\
              "{:}-{:}{:}".format(main_name,
                mitm_config.get("patch-suffix", "patched"),
                extension)

  # transform the paths in task definitions
  for t in task_list:
    fix_path(t, task_directory)

  # Create simulator.
  simulator = remote_simulator.RemoteSimulator( address=address
                                              , port=port
                                              , timeout=timeout
                                              , launch_timeout=launch_timeout
                                              , retry=retry
                                              , resize_for_transfer=resize_for_transfer
                                              )

  if unify_vocabulary is not None:
    with open(unify_vocabulary) as f:
      vocabulary = list(map(str.strip, f))
  else:
    vocabulary = None

  task_managers = list( map( functools.partial( task_manager_lib.TaskManager
                                              , start_token_mark=start_token_mark
                                              , non_start_token_mark=non_start_token_mark
                                              , special_token_pattern=special_token_pattern
                                              , fix_vocabulary_to=vocabulary
                                              , text_model=text_model
                                              , icon_model=icon_model
                                              , get_sbert=(sbert_holder or SBERTHolder()).get_sbert
                                              )
                           , task_list
                           )
                      )
  coordinator = coordinator_lib.Coordinator( simulator, task_managers
                                           , with_view_hierarchy=with_view_hierarchy
                                           , **coordinator_args
                                           )

  # Load environment.
  return environment.AndroidEnv(coordinator=coordinator)
