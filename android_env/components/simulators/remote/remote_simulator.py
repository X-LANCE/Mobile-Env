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

from android_env.components.simulators import base_simulator
from android_env.components.adb_controller import AdbController
from android_env.components.log_stream import LogStream
from android_env.components.simulators.remote import remote_base\
                                                   , remote_adb_controller\
                                                   , remote_log_stream
#from android_env.components.action_type import ActionType

import requests
from typing import Dict, List, Tuple
from typing import Optional, Union, Any
import numpy as np
import base64
from PIL import Image

from absl import logging
import traceback

# ZDY_COMMENT: adb_root and frida_server arguments are ignored here
# they should be configured directly on launching the daemon on server

class RemoteSimulator( base_simulator.BaseSimulator
                     , remote_base.RemoteBase
                     ):
    #  class RemoteSimulator {{{ # 
    """
    Protocol:
    - launching
      + init
      + launch
      + restart
      + close
    - adb
      + create_adbc
        + receives {
            "name": str
            "id": int
          }
      + adb
        + sends {
            "id": int
            "cmd": list of str
            "timeout": float or none
          }
        + receives {
            "id": int
            "output": base64 or none
          }
    - log
      + create_logs
        + text line stream
      + set_filts
        + sends {
            "filts": list of str
          }
    - act & observ.
      + act
        + sends [
            {
                "action_type": int
                "touch_position": list of float
                "input_token": int
                "response": str
            }
          ]
      + observ
        + sends {
            "resize_to": [int, int] # W, H
        }
        + receives {
            "img": base64
            "size": [int, int] # W, H
            "raw_size": [int, int] # W, H
            "time": int
          }
    """

    def __init__( self
                , address: str
                , port: int
                , timeout: float = 5.
                , launch_timeout: float = 2.
                , retry: int = 3
                , resize_for_transfer: Optional[Tuple[int, int]] = None
                , **kwargs
                ):
        #  method __init__ {{{ # 
        """
        Args:
            address (str): IP address of remote daemon
            port (int): listening port of remote daemone
            timeout (float): timeout for regular commands in secondes
            launch_timeout (float): timeout for commands `launch`, `restart`, and
              `close` in **minutes**
            retry (int): retry times
            resize_for_transfer (Optional[Tuple[int, int]]): if the screen
              should be resized for transferring as (W, H)
        """

        super(RemoteSimulator, self).__init__(**kwargs)
        #super(base_simulator.BaseSimulator, self).__init__()

        self._address: str = address
        self._port: int = port
        self._url_base = "http://{:}:{:}/".format(self._address, self._port)

        self._timeout: float = timeout
        self._launch_timeout: float = launch_timeout*60.
        self._retry: int = retry

        self._resize_for_transfer: Optional[Tuple[int, int]] = resize_for_transfer

        self._session: requests.Session = requests.Session()
        self._adb_device_name: str = "remote-device"

        self._get_response("init")
        self._adb_controller: AdbController = self.create_adb_controller()
        #  }}} method __init__ # 

    #  Setup and Clear Methods {{{ # 
    def _restart_impl(self):
        self._get_response("restart", timeout=self._launch_timeout)
    def _launch_impl(self):
        #self._session = requests.Session()
        self._get_response("launch", timeout=self._launch_timeout)
    def close(self):
        try:
            self._get_response("close", timeout=self._launch_timeout)
        except:
            logging.exception("Response Error During Closing RemoteSimulator")
            traceback.print_exc()
        self._session.close()
        super(RemoteSimulator, self).close()
    #  }}} Setup and Clear Methods # 

    def adb_device_name(self) -> str:
        #  method adb_device_name {{{ # 
        return self._adb_device_name
        #  }}} method adb_device_name # 
    def create_adb_controller(self) -> AdbController:
        #  method create_adb_controller {{{ # 
        response: requests.Response = self._get_response("create_adbc")
        response: Dict[str, Union[str, int]] = response.json()
        self._adb_device_name = response["name"]
        self._adb_device_name = "remote-device:{:}".format(self._adb_device_name)
        remote_id: int = response["id"]

        return remote_adb_controller.RemoteAdbController( self._address
                                                        , self._port
                                                        , self._session
                                                        , self._timeout
                                                        , self._retry
                                                        , remote_id
                                                        , self._adb_device_name
                                                        )
        #  }}} method create_adb_controller # 
    def _create_log_stream(self) -> LogStream:
        #  method _create_log_stream {{{ # 
        return remote_log_stream.RemoteLogStream( self._address
                                                , self._port
                                                , self._session
                                                , self._timeout
                                                , self._retry
                                                )
        #  }}} method _create_log_stream # 

    def send_action(self, action: Union[Dict[str, np.ndarray], List[Dict[str, np.ndarray]]]):
        #  method send_action {{{ # 
        if not isinstance(action, list):
          action: List[Dict[str, np.ndarray]] = [action]
        action_dicts: List[Dict[str, Any]] = []

        for act in action:
            action_dict: Dict[str, Any] = {}
            action_dict["action_type"] = act["action_type"].tolist()
            if "touch_position" in act:
                action_dict["touch_position"] = act["touch_position"].tolist()
            if "input_token" in act:
                action_dict["input_token"] = act["input_token"].tolist()
            if "response" in act:
                action_dict["response"] = act["response"].tolist()
            action_dicts.append(action_dict)

        self._get_response("act", action_dicts)
        #  }}} method send_action # 
    def _get_observation(self) -> Optional[List[np.ndarray]]:
        #  method _get_observation {{{ # 
        """
        Returns:
            np.ndarray: ndarray with shape (H, W, 3) of uint8 as the screenshot
            np.int64: the timestamp
        """

        response: requests.Response = self._get_response( "observ"
                                                        , { "resize_to": self._resize_for_transfer }\
                                                       if self._resize_for_transfer is not None else {}
                                                        )
        response: Dict[str, Any] = response.json()

        width: int
        height: int
        width, height = response["size"]
        img_buffer: bytes = base64.b64decode(response["img"].encode())
        image: np.ndarray = np.frombuffer( img_buffer
                                         , dtype=np.uint8
                                         , count=width*height*3
                                         )
        image = np.reshape(image, (height, width, 3))
        image = np.array( Image.fromarray(image).resize(response["raw_size"])
                        , dtype=np.uint8
                        )

        return [image, np.int64(response["time"])]
        #  }}} method _get_observation # 
    #  }}} class RemoteSimulator # 

if __name__ == "__main__":
    import time
    #from typing import Iterator
    from android_env.components.action_type import ActionType
    #from PIL import Image

    simulator = RemoteSimulator("127.0.0.1", 5000)
    simulator.launch()
    #simulator.restart()

    input("\x1b[31mPress ENTER to continue on ADB test.\x1b[0m")

    adb_controller: AdbController = simulator.create_adb_controller()
    adb_controller.install_apk("apps/wikihow/wikiHow：万事指南_2.9.6_apkcombo.com.apk")
    adb_controller.start_activity( "com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity"
                                 , extra_args=None
                                 )

    input("\x1b[31mPress ENTER to continue on log stream test.\x1b[0m")

    log_stream: LogStream = simulator.get_log_stream()
    log_stream.set_log_filters(["jd:D"])
    try:
        for l in log_stream.get_stream_output():
            print(l)
    except KeyboardInterrupt:
        log_stream.stop_stream()

    input("\x1b[31mPress ENTER to continue on action test.\x1b[0m")

    simulator.send_action( { "action_type": np.array(ActionType.TOUCH)
                           , "touch_position": np.array([0.17, 0.90])
                           }
                         )
    time.sleep(.005)
    simulator.send_action( { "action_type": np.array(ActionType.LIFT)
                           , "touch_position": np.empty((2,))
                           }
                         )

    input("\x1b[31mPress ENTER to continue on observation test.\x1b[0m")

    observation: Dict[str, np.ndarray] = simulator.get_observation()
    print("TD: @{:}, OT: {:}".format(observation["timedelta"], np.argmax(observation["orientation"])))
    screen = Image.fromarray(observation["pixels"])
    screen.save("a.png")

    input("\x1b[31mPress ENTER to continue on ...\x1b[0m")
    adb_controller.close()
    simulator.close()
