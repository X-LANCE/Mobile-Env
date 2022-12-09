import easyocr
from android_env.components.tools.types import TextModel

from typing import Union, Optional
import torch
import numpy as np

def EasyOCRWrapper(TextModel):
    def __init__( self
                , gpu: Union[bool, str, torch.device] = True
                , model_storage_directory: Optional[str] = None
                , download_enabled: bool = True
                ):
        #  method __init__ {{{ # 
        """
        Args:
            gpu: bool or str or torch.device to specify the model device
            model_storage_directory: optional str for the EasyOCR model path.
              EasyOCR will check the following variables in order to determine
              in which directory the model should be found:
              + `model_storage_directory`
              + $EASYOCR_MODULE_PATH
              + $MODULE_PATH
              + ~/.EasyOCR
            download_enabled: bool
        """

        self._reader: easyocr.Reader =\
                easyocr.Reader( ["en"], gpu=gpu
                              , model_storage_directory=model_storage_directory
                              , download_enabled=download_enabled
                              )
        #  }}} method __init__ # 

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

        screen = screen.cpu().numpy()
        screen = np.clip(screen*255., 0, 255).astype(np.uint8)
        screen = np.transpose(screen, (1, 2, 0))
        screen = screen[..., [2, 1, 0]]

        # TODO
        #  }}} method text_detector # 
