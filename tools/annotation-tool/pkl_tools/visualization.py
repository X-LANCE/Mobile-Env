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

"""
Created by Danyang Zhang @X-Lance.
"""

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from android_env.components import action_type

from typing import Dict
from typing import Any

# numpy array of uint8 with shape (H, W, 3) --Image.fromarray-> RGB Image

def visualize(record: Dict[str, Any], task_definition_id: str) -> Image.Image:
    """
    Args:
        record: dict like
          {
            "action_type": {0, 1, 2, 3}
            "input_token": str, present if `action_type` is 3
              (action_type.ActionType.TEXT)
            "touch_position": ndarray of float64 with shape (2,), present if
              `action_type` is not 3
            "reward": float, optional
            "instruction": list of str, optional
            "observation": ndarray of uint8 with shape (H, W, 3)
          }
        task_definition_id: str

    Return:
        Image.Image
    """

    # commonly, H = 1920, W = 1080
    height, width, _ = record["observation"].shape
    info_height = 400
    canvas = Image.new("RGB", (width, height + info_height), color="white")

    canvas.paste(Image.fromarray(record["observation"]))

    drawer = ImageDraw.Draw(canvas, mode="RGBA")
    font = ImageFont.truetype("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc", size=50)

    title_anchor = (10, height+10)
    drawer.text( title_anchor, task_definition_id
               , fill=(0, 0, 0, 255), font=font
               )
    title_bbox = drawer.textbbox( title_anchor
                                , task_definition_id
                                , font=font
                                )

    action_anchor = (10, title_bbox[3]+10)
    if record["action_type"]==action_type.ActionType.TEXT:
        drawer.rectangle( (width/5., .75*height, .8*width, 0.9375*height)
                        , fill=(135, 135, 135, 127)
                        )
        drawer.text( (width/2., 0.84375*height), record["input_token"]
                   , fill=(0, 0, 0, 229), font=font, anchor="mm"
                   )

        action_text = "TEXT({:})".format(record["input_token"])
    elif record["action_type"]==action_type.ActionType.TOUCH:
        x, y = record["touch_position"]
        x *= width
        y *= height
        r0 = 20
        r1 = 50
        drawer.ellipse( (x-r1, y-r1, x+r1, y+r1)
                      , fill=(255, 175, 175, 76)
                      )
        drawer.ellipse( (x-r0, y-r0, x+r0, y+r0)
                      , fill=(255, 175, 175, 153)
                      )

        action_text = "TOUCH({:.2f}, {:.2f})".format(x, y)
    else:
        action_text = "{:}".format(str(action_type.ActionType(record["action_type"])))
    drawer.text( action_anchor, action_text
               , fill=(0, 0, 0, 255), font=font
               )
    text_bbox = drawer.textbbox( action_anchor
                               , action_text
                               , font=font
                               )

    if "instruction" in record:
        text_anchor = (10, text_bbox[3]+10)
        text = " ".join(record["instruction"])
        drawer.text( text_anchor, text
                   , fill=(255, 0, 0, 255), font=font
                   )
        text_bbox = drawer.textbbox( text_anchor
                                   , text
                                   , font=font
                                   )
    if "reward" in record and record["reward"]>0:
        text_anchor = (10, text_bbox[3]+10)
        text = "Reward: +{:.1f}".format(record["reward"])
        drawer.text( text_anchor, text
                   , fill=(0, 255, 0, 255), font=font
                   )

    return canvas
