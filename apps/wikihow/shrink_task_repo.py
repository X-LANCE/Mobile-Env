#!/usr/bin/python3

import os
import itertools
import numpy as np

in_path = "templates.out/"
out_path = "templates.miniout"

textprotos = filter(lambda f: f.endswith(".textproto"), os.listdir(in_path))
textprotos = filter(lambda f: "-" not in f[:-12], textprotos)
textprotos = filter(lambda f: not f.startswith("_"), textprotos)
textprotos = filter(lambda f: not f[:-12].endswith("_"), textprotos)
textprotos = list(textprotos)

#textprotos = sorted(textprotos, key=(lambda f: f[-11]))
#textprotos = itertools.groupby(textprotos, key=(lambda f: f[-11]))
#textprotos = {k: list(gr) for k, gr in textprotos}
weight_dict = { "0": 5
              , "4": 2
              , "6": 2
              , "7": 4
              , "8": 5
              }
weights = list(map(lambda f: weight_dict[f[-11]], textprotos))

textprotos = np.array(textprotos)
#print(textprotos.shape, textprotos.dtype)
weights = np.array(weights)
rng = np.random.default_rng()
samples = rng.choice(textprotos, size=(200,), replace=False, p=weights/np.sum(weights))
with open("templates.miniout.list", "w") as f:
    for spl in samples:
        print(spl, file=f)
