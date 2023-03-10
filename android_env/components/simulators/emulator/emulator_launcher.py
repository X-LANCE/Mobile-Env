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

"""Prepares and launches the emulator."""

import os
import subprocess
import time
from typing import Optional

from absl import logging
from android_env.components import errors
import grpc

from android_env.proto import emulator_controller_pb2
from android_env.proto import emulator_controller_pb2_grpc
from google.protobuf import empty_pb2

# Period in milliseconds to ping the Emulator gRPC server to keep the connection
# alive. If too frequent, we may get errors such as "Too many pings.", which can
# bring down the process.
_GRPC_KEEPALIVE_MS = 100000

class EmulatorLauncher():
  """Handles launching the emulator."""

  def __init__(
      self,
      local_tmp_dir: str = '/tmp',
      adb_port: Optional[int] = None,
      adb_server_port: Optional[int] = None,
      emulator_console_port: Optional[int] = None,
      grpc_port: int = -1,
      emulator_path: str = '',
      android_sdk_root: str = '',
      avd_name: str = '',
      run_headless: bool = False,
      kvm_device: str = '/dev/kvm',
      gpu_mode: str = 'swiftshader_indirect',
      android_avd_home: str = '',
      startup_wait_time_sec: int = 300,
      writable_system: bool = False,
      proxy_address: Optional[str] = None,
      proxy_port: Optional[str] = None):
    """Installs required files locally and launches the emulator.

    Args:
      local_tmp_dir: Local directory for logs and maybe installing the AVD.
      adb_port: ADB port for the Android device.
      adb_server_port: Port of the ADB server deamon.
      emulator_console_port: Port for telnet communication with the emulator.
      grpc_port: Port for gRPC communication with the emulator.
      emulator_path: Path to the emulator binary.
      android_sdk_root: Root directory of the Android SDK.
      avd_name: Name of the AVD.
      run_headless: Whether to run in headless mode.
      kvm_device: Path to the KVM device.
      gpu_mode: GPU mode override. Supported values are listed at:
        https://developer.android.com/studio/run/emulator-acceleration#accel-graphics
      android_avd_home: Local directory for AVDs.
      startup_wait_time_sec: Timeout for booting the emulator.
      writable_system: Whether to run with a writable /system partition.
      proxy_address: The address for the HTTP proxy.
      proxy_port: The port for the HTTP proxy.
    """
    self._local_tmp_dir: str = local_tmp_dir
    self._adb_port: Optional[int] = adb_port
    self._adb_server_port: Optional[int] = adb_server_port
    self._emulator_console_port: Optional[int] = emulator_console_port
    self._emulator_path: str = emulator_path
    self._android_sdk_root: str = android_sdk_root
    self._avd_name: str = avd_name
    self._run_headless: bool = run_headless
    self._writable_system: bool = writable_system
    self._kvm_device: str = kvm_device
    self._gpu_mode: str = gpu_mode
    self._android_avd_home: str = android_avd_home
    self._startup_wait_time_sec: int = startup_wait_time_sec
    self._grpc_port: int = grpc_port
    self._proxy_address: Optional[str] = proxy_address
    self._proxy_port: Optional[str] = proxy_port

    self._emulator = None
    self._emulator_output = None
    self._emulator_stub = None
    self._is_closed = False

  def launch(self) -> None:
    """Launches the emulator."""

    logging.info('Booting the emulator [%s]', self._emulator_path)

    # Set necessary environment variables.
    base_lib_dir = self._emulator_path[:-8] + 'lib64/'
    ld_library_path = ':'.join([
        base_lib_dir + 'x11/',
        base_lib_dir + 'qt/lib/',
        base_lib_dir + 'gles_swiftshader/',
        base_lib_dir
    ])
    extra_env_vars = {
        'ANDROID_HOME': '',
        'ANDROID_SDK_ROOT': self._android_sdk_root,
        'ANDROID_AVD_HOME': self._android_avd_home,
        'ANDROID_EMULATOR_KVM_DEVICE': self._kvm_device,
        'ANDROID_ADB_SERVER_PORT': str(self._adb_server_port),
        'LD_LIBRARY_PATH': ld_library_path,
        'QT_DEBUG_PLUGINS': '1',
        'QT_XKB_CONFIG_ROOT': str(self._emulator_path[:-8] + 'qt_config/'),
    }
    logging.info('extra_env_vars: %s', str(extra_env_vars))
    env_vars = dict(os.environ).copy()
    env_vars.update(extra_env_vars)

    # Compile command.
    grpc_port = ['-grpc', str(self._grpc_port)] if self._grpc_port >= 0 else []
    run_headless = ['-no-skin', '-no-window'] if self._run_headless else []
    writable_system = ["-writable-system"] if self._writable_system else []
    ports = ['-ports', '%s,%s' % (self._emulator_console_port, self._adb_port)]
    proxy = ["-http-proxy", "http://{:}:{:}".format(self._proxy_address, self._proxy_port)]\
            if self._proxy_address and self._proxy_port else []
    command = [
        self._emulator_path,
        '-no-snapshot',
        '-read-only',
        '-gpu', self._gpu_mode,
        '-no-audio',
        '-verbose',
        '-avd', self._avd_name,
    ] + grpc_port + run_headless + writable_system + ports + proxy
    logging.info('Emulator launch command: %s', ' '.join(command))

    # Prepare logfile.
    emulator_logfile = os.path.join(self._local_tmp_dir, 'emulator_output')
    self._emulator_output = open(emulator_logfile, 'wb')

    # Spawn the emulator process.
    self._emulator = subprocess.Popen(
        command,
        env=env_vars,
        stdout=self._emulator_output,
        stderr=self._emulator_output)

    self._emulator_stub = EmulatorLauncher.create_emulator_stub(self._grpc_port)

    # Wait for the emulator to boot.
    start_time = time.time()
    deadline = start_time + self._startup_wait_time_sec
    success = False
    while time.time() < deadline:
      emu_status = self._emulator_stub.getStatus(empty_pb2.Empty())
      logging.info('Waiting for emulator to start. Emulator uptime: %rms',
                   emu_status.uptime)
      if emu_status.booted:
        success = True
        break
      time.sleep(5.0)

    elapsed_time = time.time() - start_time
    if not success:
      raise errors.SimulatorCrashError(
          'The emulator failed to boot after %r seconds' %
          self._startup_wait_time_sec)

    logging.info('Done booting the emulator (in %f seconds).', elapsed_time)

  def restart(self) -> None:
    logging.info('Restarting the emulator...')
    self._kill_emulator_process()
    self.launch()
    logging.info('Done restarting the emulator.')

  @classmethod
  def create_emulator_stub(
      cls,
      grpc_port: int,
      use_async: bool = False,
  ) -> emulator_controller_pb2_grpc.EmulatorControllerStub:
    """Returns a stub to the EmulatorController service."""
    logging.info('Creating gRPC channel to the emulator on port %r', grpc_port)
    port = f'localhost:{grpc_port}'
    options = [('grpc.max_send_message_length', -1),
               ('grpc.max_receive_message_length', -1),
               ('grpc.keepalive_time_ms', _GRPC_KEEPALIVE_MS)]
    creds = grpc.local_channel_credentials()
    if use_async:
      channel = grpc.aio.secure_channel(port, creds, options=options)
    else:
      channel = grpc.secure_channel(port, creds, options=options)
    grpc.channel_ready_future(channel).result()  # Wait for channel to be ready.
    logging.info('Added gRPC channel for the Emulator on port %s', port)
    return emulator_controller_pb2_grpc.EmulatorControllerStub(channel)

  def get_emulator_stub(
      self) -> emulator_controller_pb2_grpc.EmulatorControllerStub:
    """Returns the EmulatorController stub for the launched emulator."""
    return self._emulator_stub

  def _kill_emulator_process(self) -> None:
    """Shuts down the emulator process."""
    if self._emulator:
      logging.info('Killing the emulator process...')
      self._emulator_stub.setVmState(
          emulator_controller_pb2.VmRunState(
              state=emulator_controller_pb2.VmRunState.RunState.SHUTDOWN))
      logging.info('Will wait 30s for it to finish gracefully...')
      try:
        self._emulator.wait(timeout=30.0)
      except subprocess.TimeoutExpired:
        logging.exception(
            'The emulator process did not finish after 30s. '
            'returncode: %s. Will now try to kill() it.',
            self._emulator.returncode)
        self._emulator.kill()
      self._emulator = None
      self._emulator_output.close()
      logging.info('Done killing the emulator process.')

  def close(self):
    """Clean up launcher files and processes."""
    if not self._is_closed:
      self._kill_emulator_process()
      self._is_closed = True

  def __del__(self):
    self.close()
