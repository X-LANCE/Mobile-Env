#/usr/bin/python3

import sys
sys.path.append("../")

from android_env.proto import emulator_controller_pb2_grpc
import grpc
from android_env.components.adb_controller import AdbController
from google.protobuf import empty_pb2

from android_env.proto import emulator_controller_pb2
#import numpy as np

#from PIL import Image
#from utils.misc import som_preprocess
#import easyocr
#from utils.vision_ui import ImageInfer
#from utils.vision_ui.config import IMAGE_INFER_MODEL_PATH
#import os.path
#import time
import datetime

port = sys.argv[1]
channel = grpc.secure_channel( "127.0.0.1:{:}".format(port), grpc.local_channel_credentials()
                             , options = [ ('grpc.max_send_message_length', -1)
                                         , ('grpc.max_receive_message_length', -1)
                                         , ('grpc.keepalive_time_ms', 10_0000)
                                         ]
                             )
grpc.channel_ready_future(channel).result()
stub = emulator_controller_pb2_grpc.EmulatorControllerStub(channel)

adb_controller = AdbController(device_name="emulator-5554", prompt_regex=r'\w*:\/ [$#]')

#image_proto = stub.getScreenshot( emulator_controller_pb2.ImageFormat(
                                    #format=emulator_controller_pb2.ImageFormat.RGB888
                                  #, height=1920
                                  #, width=1080
                                  #)
                                #)
#image = np.frombuffer( image_proto.image, dtype=np.uint8
                     #, count=image_proto.format.height*image_proto.format.width*3
                     #)
#image.shape = (image_proto.format.height, image_proto.format.width, 3)
#image = Image.fromarray(image)
#image = image.resize((280, 500))
#image = som_preprocess(image, easyocr.Reader(["en"]), ImageInfer(os.path.join("..", IMAGE_INFER_MODEL_PATH)))[0]
#image.show()

start: float = datetime.datetime.now().timestamp()
print(start)
#stub.sendKey( emulator_controller_pb2.KeyboardEvent(
                ##codeType=emulator_controller_pb2.KeyboardEvent.KeyCodeType.Evdev
                #eventType=emulator_controller_pb2.KeyboardEvent.KeyEventType.keypress
              #, text="How to 180 on board"
              #)
            #)
original_clipboard: emulator_controller_pb2.ClipData = stub.getClipboard(empty_pb2.Empty())
returned: empty_pb2.Empty = stub.setClipboard( emulator_controller_pb2.ClipData(
                    text="这样可以吗？"
                  )
                 )
#print(returned)
#exit()
adb_controller._execute_command(["shell", "input", "keyevent", "KEYCODE_PASTE"])
stub.setClipboard(original_clipboard)
# https://developer.mozilla.org/en-US/docs/Web/API/UI_Events/Keyboard_event_code_values
# XKB is Linux (X11)
# EvDev is Android
#codeType = emulator_controller_pb2.KeyboardEvent.KeyCodeType.Evdev
#stub.sendKey( emulator_controller_pb2.KeyboardEvent(
                #codeType=codeType
              #, eventType=emulator_controller_pb2.KeyboardEvent.KeyEventType.keypress
              #, keyCode=0x87
              #)
            #)
#time.sleep(1.)
#stub.sendKey( emulator_controller_pb2.KeyboardEvent(
                #codeType=codeType
              #, eventType=emulator_controller_pb2.KeyboardEvent.KeyEventType.keyup
              #, keyCode=0x87
              #)
            #)
end: float = datetime.datetime.now().timestamp()
print("{:} - {:} = {:}".format(end, start, end-start))
