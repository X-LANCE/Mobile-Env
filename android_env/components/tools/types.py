import abc
import torch
from typing import List, Tuple

class TextModel(abc.ABC):
    def text_detector( self
                     , screen: torch.Tensor
                     , bboxes: List[torch.Tensor]
                     ) -> List[List[str]]:
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width)
            bboxes: list with length nb_bboxes of torch.Tensor of float32 with shape (1, 4)

        Returns:
            list with length nb_bboxes of list of str
        """

        return [[] for _ in bboxes]
    def text_recognizer( self
                       , screen: torch.Tensor
                       , bboxes: List[torch.Tensor]
                       ) -> List[str]:
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width)
            bboxes: list with length nb_bboxes of torch.Tensor of float32 with shape (1, 4)

        Returns:
            list with length nb_bboxes of str
        """

        return ["" for _ in bboxes]

class IconModel(abc.ABC):
    def icon_detector( self
                     , screen: torch.Tensor
                     , bboxes: List[torch.Tensor]
                     ) -> Tuple[ torch.Tensor
                               , List[List[str]]
                               ]:
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width)
            bboxes: list with length nb_bboxes of torch.Tensor of float32 with shape (1, 4)

        Returns:
            - torch.Tensor of float with shape (nb_bboxes, nb_candidates, 4)
            - list with length nb_bboxes of list with length nb_candidates of
              str as the icon classes
        """

        return torch.stack(bboxes)\
             , [[""] for _ in bboxes]
    def icon_recognizer( self
                       , screen: torch.Tensor
                       , bboxes: List[torch.Tensor]
                        ) -> List[str]:
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width)
            bboxes: list with length nb_bboxes of torch.Tensor of float32 with shape (1, 4)

        Returns:
            list with length nb_bboxes of str
        """

        return ["" for _ in bboxes]
    def icon_matcher( self
                    , screen: torch.Tensor
                    , targets: List[torch.Tensor]
                    , bboxes: torch.Tensor
                    ) -> List[List[bool]]:
        """
        Args:
            screen: torch.Tensor of float32 with shape (3, height, width)
            targets: list with length nb_bboxes of torch.Tensor of float32 with
              shape (3, height', width')
            bboxes: torch.Tensor of float32 with shape (nb_bboxes, nb_candidates, 4)

        Returns:
            list with length nb_bboxes of list with length nb_candidates of bool
        """

        return [[False for _ in bb] for bb in bboxes]
