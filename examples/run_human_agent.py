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

"""Loads an interactive session where a human acts on behalf of an agent."""

import time
from typing import Any, Optional, Union
from typing import Dict, List, Tuple
import pickle as pkl

from absl import app
from absl import flags
from absl import logging
import android_env
from android_env.components import action_type
from android_env.components import utils
from android_env.proto import adb_pb2
from android_env.proto import task_pb2
import dm_env
import numpy as np
import pygame

# Simulator args.
flags.DEFINE_string('avd_name', None, 'Name of AVD to use.')
flags.DEFINE_string('android_avd_home', '~/.android/avd', 'Path to AVD.')
flags.DEFINE_string('android_sdk_root', '~/Android/Sdk', 'Path to SDK.')
flags.DEFINE_string('emulator_path',
                    '~/Android/Sdk/emulator/emulator', 'Path to emulator.')
flags.DEFINE_string('adb_path',
                    '~/Android/Sdk/platform-tools/adb', 'Path to ADB.')
flags.DEFINE_boolean('run_headless', True, 'Optionally turn off display.')

flags.DEFINE_enum("mitm", "none", [
    "none",
    "syscert",
    "frida",
    "packpatch"
  ], "Mitm method")
flags.DEFINE_string("frida_script", "frida-script.js", "Path to frida script.")

# Environment args.
flags.DEFINE_string('task_path', None, 'Path to task textproto file.')

# Pygame args.
flags.DEFINE_list('screen_size', '480,720', 'Screen width, height in pixels.')
flags.DEFINE_float('frame_rate', 1.0/30.0, 'Frame rate in seconds.')

FLAGS = flags.FLAGS

key_to_integer = {
    pygame.K_0: 0,
    pygame.K_1: 1,
    pygame.K_2: 2,
    pygame.K_3: 3,
    pygame.K_4: 4,
    pygame.K_5: 5,
    pygame.K_6: 6,
    pygame.K_7: 7,
    pygame.K_8: 8,
    pygame.K_9: 9,
    pygame.K_KP0: 0,
    pygame.K_KP1: 1,
    pygame.K_KP2: 2,
    pygame.K_KP3: 3,
    pygame.K_KP4: 4,
    pygame.K_KP5: 5,
    pygame.K_KP6: 6,
    pygame.K_KP7: 7,
    pygame.K_KP8: 8,
    pygame.K_KP9: 9
  }

def _get_action_from_event(
    event: pygame.event.Event,
    screen: pygame.Surface,
    orientation: adb_pb2.AdbCall.Rotate.Orientation,
    vocabulary_size: int) -> Union[int, Dict[str, Any]]:
  """Returns the current action by reading data from a pygame Event object."""

  if event.type==pygame.KEYDOWN:
    if event.key==pygame.K_ESCAPE:
      return 0
    if event.key in key_to_integer and vocabulary_size>0:
      return {
          "action_type": np.array(action_type.ActionType.TEXT, dtype=np.int32),
          "input_token": np.clip(np.array(key_to_integer[event.key], dtype=np.int32), 0, vocabulary_size-1)
        }
  elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
    act_type = action_type.ActionType.LIFT
    if event.type == pygame.MOUSEBUTTONDOWN:
      act_type = action_type.ActionType.TOUCH

    return {
        'action_type':
            np.array(act_type, dtype=np.int32),
        'touch_position':
            _scale_position(event.pos, screen, orientation),
    }


def _get_action_from_mouse(
    screen: pygame.Surface,
    orientation: adb_pb2.AdbCall.Rotate.Orientation) -> Dict[str, Any]:
  """Returns the current action by reading data from the mouse."""

  act_type = action_type.ActionType.LIFT
  if pygame.mouse.get_pressed()[0]:
    act_type = action_type.ActionType.TOUCH

  return {
      'action_type':
          np.array(act_type, dtype=np.int32),
      'touch_position':
          _scale_position(pygame.mouse.get_pos(), screen, orientation),
  }


def _scale_position(
    position: np.ndarray,
    screen: pygame.Surface,
    orientation: adb_pb2.AdbCall.Rotate.Orientation) -> np.ndarray:
  """AndroidEnv accepts mouse inputs as floats so we need to scale it."""

  scaled_pos = np.divide(position, screen.get_size(), dtype=np.float32)
  if orientation == adb_pb2.AdbCall.Rotate.Orientation.LANDSCAPE_90:
    scaled_pos = scaled_pos[::-1]
    scaled_pos[0] = 1 - scaled_pos[0]
  return scaled_pos


def _accumulate_reward(
    timestep: dm_env.TimeStep,
    episode_return: float) -> float:
  """Accumulates rewards collected over the course of an episode."""

  if timestep.reward and timestep.reward != 0:
    logging.info('Reward: %s', timestep.reward)
    episode_return += timestep.reward

  if timestep.first():
    episode_return = 0
  elif timestep.last():
    logging.info('Episode return: %s', episode_return)

  return episode_return


def _render_pygame_frame(
    surface: pygame.Surface,
    screen: pygame.Surface,
    orientation: adb_pb2.AdbCall.Rotate.Orientation,
    timestep: dm_env.TimeStep) -> None:
  """Displays latest observation on pygame surface."""

  frame = timestep.observation['pixels'][:, :, :3]  # (H x W x C) (RGB)
  frame = utils.transpose_pixels(frame)  # (W x H x C)
  frame = utils.orient_pixels(frame, orientation)

  pygame.surfarray.blit_array(surface, frame)
  pygame.transform.smoothscale(surface, screen.get_size(), screen)

  pygame.display.flip()

class Recorder():
  #  class `Recorder` {{{ # 
  def __init__(self, dump_file: str):
    self.dump_file: str = dump_file
    self.prev_type: action_type.ActionType = action_type.ActionType.LIFT

    self.trajectories:\
      List[List[Dict[str, Any]]]\
        = []
    self.current_trajectory:\
      List[Dict[str, Any]]\
        = []

  def __enter__(self):
    return self
  def __exit__(self, *args):
    if len(self.current_trajectory)>0:
      self.trajectories.append(self.current_trajectory)

    with open(self.dump_file, "wb") as f:
      pkl.dump(self.trajectories, f)
    logging.info("\x1b[32mDUMPED TRAJECTORY RECORDS\x1b[0m")

  def log(self,
      action: Dict[str, np.ndarray],
      timestep: dm_env.TimeStep):
    current_type = action["action_type"].item()
    if current_type==action_type.ActionType.LIFT\
        and self.prev_type==action_type.ActionType.LIFT:
      return

    record = {}
    record["action_type"] = current_type
    if current_type==action_type.ActionType.TEXT:
      record["input_token"] = action["input_token"].item()
    elif current_type==action_type.ActionType.TOUCH:
      record["touch_position"] = action["touch_position"]
    #record["reward"] = timestep.reward
    #record["observation"] = timestep.observation["pixels"]
    #record["orientation"] = np.argmax(timestep.observation["orientation"])
    self.current_trajectory.append(record)

    if timestep.last():
      self.trajectories.append(self.current_trajectory)
      self.current_trajectory = []
  #  }}} class `Recorder` # 

def main(_):

  pygame.init()
  pygame.display.set_caption('android_human_agent')

  if FLAGS.mitm=="none":
    mitm_config = None
  else:
    mitm_config = {"method": FLAGS.mitm}
  if FLAGS.mitm=="frida":
    mitm_config["frida-script"] = FLAGS.frida_script

  with android_env.load(
        emulator_path=FLAGS.emulator_path,
        android_sdk_root=FLAGS.android_sdk_root,
        android_avd_home=FLAGS.android_avd_home,
        avd_name=FLAGS.avd_name,
        adb_path=FLAGS.adb_path,
        task_path=FLAGS.task_path,
        run_headless=FLAGS.run_headless,
        mitm_config=mitm_config) as env,\
      Recorder("action_record.pkl") as recorder:

    action_specification = env.action_spec()
    vocabulary_size = action_specification["input_token"].num_values if "input_token" in action_specification\
        else 0

    # Reset environment.
    first_timestep = env.reset()
    orientation = np.argmax(first_timestep.observation['orientation'])

    # Create pygame canvas.
    screen_size = list(map(int, FLAGS.screen_size))  # (W x H)
    obs_shape = env.observation_spec()['pixels'].shape[:2]  # (H x W)

    if (orientation == adb_pb2.AdbCall.Rotate.Orientation.LANDSCAPE_90 or
        orientation == adb_pb2.AdbCall.Rotate.Orientation.LANDSCAPE_270):
      screen_size = screen_size[::-1]
      obs_shape = obs_shape[::-1]

    screen = pygame.display.set_mode(screen_size)  # takes (W x H)
    surface = pygame.Surface(obs_shape[::-1])  # takes (W x H)

    # Start game loop.
    prev_frame = time.time()
    episode_return = 0

    #record_file = open("action_record.txt", "w")

    breaks = False
    #prev_type = action_type.ActionType.LIFT
    while True:
      #if pygame.key.get_pressed()[pygame.K_ESCAPE]:
        #return

      all_events = pygame.event.get()
      for event in all_events:
        if event.type == pygame.QUIT:
          breaks = True
          break

      # Filter event queue for mouse click events.
      #mouse_click_events = [
          #event for event in all_events
          #if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]
      #]

      # Process all mouse click events.
      #for event in mouse_click_events:
      for event in all_events:
        action = _get_action_from_event(event, screen, orientation, vocabulary_size)
        if action==0:
          breaks = True
          break
        if action is None:
          continue
        timestep = env.step(action)
        recorder.log(action, timestep)

        reward = timestep.reward
        instruction = env.task_instructions()
        #logging.info('reward: %r, \x1b[31;42minstruct\x1b[0m: %r', reward, instruction)
        episode_return = _accumulate_reward(timestep, episode_return)
        _render_pygame_frame(surface, screen, orientation, timestep)

      if breaks:
        break

      # Sample the current position of the mouse either way.
      action = _get_action_from_mouse(screen, orientation)
      timestep = env.step(action)
      recorder.log(action, timestep)

      reward = timestep.reward
      instruction = env.task_instructions()
      #logging.info('reward: %r, \x1b[31;42minstruct\x1b[0m: %r', reward, instruction)
      episode_return = _accumulate_reward(timestep, episode_return)
      _render_pygame_frame(surface, screen, orientation, timestep)

      # Limit framerate.
      now = time.time()
      frame_time = now - prev_frame
      if frame_time < FLAGS.frame_rate:
        time.sleep(FLAGS.frame_rate - frame_time)
      prev_frame = now

  logging.info("\x1b[1;31mCLOSED 1!\x1b[0m")
  pygame.quit()
  logging.info("\x1b[1;31mCLOSED 2!\x1b[0m")
  return


if __name__ == '__main__':
  logging.set_verbosity('info')
  logging.set_stderrthreshold('info')
  flags.mark_flags_as_required(['avd_name', 'task_path'])
  app.run(main)
