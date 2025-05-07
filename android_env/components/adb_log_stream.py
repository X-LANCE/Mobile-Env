# coding=utf-8
# vim: set tabstop=2 shiftwidth=2 expandtab:
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

"""Class for a stream of logs output by a locally running emulator."""

import subprocess
from typing import List

from android_env.components import log_stream


_LOGCAT_COMMAND = ['logcat', '-v', 'epoch']


class AdbLogStream(log_stream.LogStream):
  """Manages adb logcat process for a locally running emulator."""

  def __init__(self, adb_command_prefix: List[str], *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._adb_command_prefix = adb_command_prefix

  def _get_stream_output(self):
    cmd = self._adb_command_prefix + _LOGCAT_COMMAND + self._filters
    self._adb_subprocess = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True)
    return self._adb_subprocess.stdout

  def stop_stream(self):
    self._adb_subprocess.kill()
