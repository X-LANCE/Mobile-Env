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

from sentence_transformers import SentenceTransformer
from typing import Optional

class SBERTHolder:
    def __init__(self, model: str = "all-MiniLM-L12-v2"):
        self._model: str = model
        self._sbert: Optional[SentenceTransformer] = None

    def get_sbert(self) -> SentenceTransformer:
        if self._sbert is None:
            self._sbert = SentenceTransformer(self._model)
        return self._sbert
