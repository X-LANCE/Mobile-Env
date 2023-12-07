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

import easyocr
from android_env.components.tools.types import TextModel

from typing import Union, Optional
from typing import List, Tuple
import threading

import torch
import numpy as np

from absl import logging
import traceback
import io

def in_bbox(bbox0: torch.Tensor, bbox1: torch.Tensor) -> torch.Tensor:
    """
    Test if `bbox0` is contained in `bbox1`.

    Args:
        bbox0 - torch.Tensor of float32 with shape (m, 4)
        bbox1 - torch.Tensor of float32 with shape (n, 4)

    Returns:
        torch.Tensor of bool with shape (n, m)
    """

    bbox0 = bbox0[None, :, :] # (1, m, 4)
    bbox1 = bbox1[:, None, :] # (n, 1, 4)

    left_side = bbox0[..., 0]>=bbox1[..., 0] # (n, m)
    up_side = bbox0[..., 1]>=bbox1[..., 1] # (n, m)
    right_side = bbox0[..., 2]<=bbox1[..., 2] # (n, m)
    down_side = bbox0[..., 3]<=bbox1[..., 3] # (n, m)

    return torch.logical_and( left_side.logical_and(up_side)
                            , right_side.logical_and(down_side)
                            )

class EasyOCRWrapper(TextModel):
    def __init__( self
                , lang_list: List[str] = ["en"]
                , gpu: Union[bool, str, torch.device] = True
                , model_storage_directory: Optional[str] = None
                , download_enabled: bool = True
                , reader: Optional[easyocr.Reader] = None
                ):
        #  method __init__ {{{ # 
        """
        Args:
            lang_list (List[str]): language list
            gpu (Union[bool, str, torch.device]): bool or str or torch.device
              to specify the model device
            model_storage_directory (Optional[sr]: optional str for the EasyOCR
              model path.  EasyOCR will check the following variables in order
              to determine in which directory the model should be found:
              + `model_storage_directory`
              + $EASYOCR_MODULE_PATH
              + $MODULE_PATH
              + ~/.EasyOCR
            download_enabled (bool): if the model should be downloaded while
              not present

            reader (Optional[easyocr.Reader]): an easyocr reader instance. if
              `reader` is provided, the other parameters will be omitted.
        """

        self._reader: easyocr.Reader = reader\
                                    or easyocr.Reader( lang_list, gpu=gpu
                                                     , model_storage_directory=model_storage_directory
                                                     , download_enabled=download_enabled
                                                     )
        self._lock: threading.Lock = threading.Lock()
        #  }}} method __init__ # 

    def _convert_screen(self, screen: torch.Tensor) -> np.ndarray:
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width) as
              the RGB image

        Returns:
            np.ndarray of uint8 with shape (height, width, 3) as the BGR image
        """

        screen = screen.cpu().numpy()
        screen = np.clip(screen*255., 0, 255).astype(np.uint8) # convert to uint8
        screen = np.transpose(screen, (1, 2, 0)) # convert (3, H, W) to (H, W, 3)
        screen = screen[..., [2, 1, 0]] # convert RGB to BGR
        return screen

    def text_detector( self
                     , screen: torch.Tensor
                     , bboxes: List[torch.Tensor]
                     ) -> List[List[str]]:
        #  method text_detector {{{ # 
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width)
            bboxes: list with length nb_bboxes of torch.Tensor of float32 with shape (1, 4)

        Returns:
            list with length nb_bboxes of list of str
        """

        try:
            logging.debug("EasyOCR Starts.")

            screen = self._convert_screen(screen) # (H, W, 3)
            with self._lock:
                results: List[ Tuple[ List[List[float]] # [x1, y1], [x2, y1], [x2, y2], [x1, y2]
                                    , str
                                    , float
                                    ]
                             ] = self._reader.readtext(screen) # get all results

            logging.debug("Screen begins")
            for bbox, t, _ in results:
                logging.debug( "[%.2f, %.2f, %.2f, %.2f]: %s"
                             , bbox[0][0], bbox[0][1]
                             , bbox[1][0], bbox[2][1]
                             , t
                             )
            logging.debug("Screen ends")

            # check the bboxes
            target_bboxes = torch.cat(bboxes) # (N, 4); N is nb_bboxes
            result_bboxes = torch.tensor(
                                list( map( lambda bb: [bb[0][0], bb[0][1], bb[1][0], bb[2][1]] # [x1, y1, x2, y2]
                                         , map( lambda rst: rst[0]
                                              , results
                                              )
                                         )
                                    )
                                ) # (M, 4); M is the number of results
            region_mask = in_bbox(result_bboxes, target_bboxes) # (N, M)

            result_texts = list( map( lambda rst: rst[1]
                                    , results
                                    )
                               )
            final_returns = []
            for m in region_mask:
                final_returns.append([t for t, m_ in zip(result_texts, m) if m_])

            logging.debug("EasyOCR Ends.")
        except Exception as e:
            with io.StringIO() as bfr:
                traceback.print_exc(file=bfr)
                logging.debug("%s", bfr.getvalue())
            raise e
        return final_returns
        #  }}} method text_detector # 

    def text_recognizer( self
                       , screen: torch.Tensor
                       , bboxes: List[torch.Tensor]
                       ) -> List[str]:
        #  method text_recognizer {{{ # 
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width)
            bboxes: list with length nb_bboxes of torch.Tensor of float32 with shape (1, 4)

        Returns:
            list with length nb_bboxes of str
        """

        screen = self._convert_screen(screen) # (H, W, 3)
        with self._lock:
            results = self._reader.readtext(screen)

        # check the bboxes
        target_bboxes = torch.cat(bboxes) # (N, 4); N is nb_bboxes
        result_bboxes = torch.tensor(
                            list( map( lambda bb: [bb[0][0], bb[0][1], bb[1][0], bb[2][1]]
                                     , map( lambda rst: rst[0]
                                          , results
                                          )
                                     )
                                )
                            ) # (M, 4); M is the number of results
        region_mask = in_bbox(result_bboxes, target_bboxes) # (N, M)

        result_texts = list( map( lambda rst: rst[1]
                                , results
                                )
                           )
        final_returns = []
        for m in region_mask:
            final_returns.append(" ".join((t for t, m_ in zip(result_texts, m) if m_)))
        return final_returns
        #  }}} method text_recognizer # 
