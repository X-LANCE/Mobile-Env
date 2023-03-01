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
