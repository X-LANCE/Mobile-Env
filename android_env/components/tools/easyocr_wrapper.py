import easyocr
from android_env.components.tools.types import TextModel

from typing import Union, Optional
from typing import List
import torch
import numpy as np

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

    def _convert_screen(screen: torch.Tensor) -> np.ndarray:
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

        screen = self._convert_screen(screen) # (H, W, 3)
        results = self._reader.readtext(screen) # get all results

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
            final_returns.append([t for t, m_ in zip(result_texts, m) if m_])
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
