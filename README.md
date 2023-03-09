<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```bibtex', '```', 'bib', 'NonText'): -->

# Mobile-Env: A Universal Platform for Training and Evaluation of Mobile Interaction

Mobile-Env is a novel interaction platform for training and evaluation of the
interaction of information user interface (InfoUI). The information user
interface is referred to as the UI comprising rich text contents interleaved
with other types of media and structured spatially with different styles, which
is fairly different from the environments in the existing control topics like
embodied robots, video game playing, text-based game playing, *etc*. A demo
video for Mobile-Env is available at <https://youtu.be/gKV6KZYwxGY>.

Mobile-Env is developed based on
[AndroidEnv](https://github.com/deepmind/android_env). The agent can take the
screenshot and the view hierarchy (disabled defaultly for the long latency) as
the observation and take a touch or type a token as the action to interact with
the Android apps. Several task events like rewards, step instructions, or the
episode end will be informed during interaction at some crucial steps. A
so-called crucial step may be opening a target page, srolling to a correct
area, *etc*. and is depending on the specific task definition. <!-- TODO: task
definition guide -->

<!-- TODO: Chinese docs -->

## Index

<!-- TODO: the subsection of documents -->

* Training and Evaluating Agents on Mobile-Env
* Extending a New App or a New Task Based on Mobile-Env
* Solution for Dynamic Information Apps
* Other Assistant Tools

## Environment Features

Mobile-Env is a flexible, adaptable, and easily-extendable platform for InfoUI
interaction with the following features:

* Screenshots and view hierarchies are provided as the observations and the
  touch and token typing are provided as the actions, which are common and
  adaptable to various apps. Environment wrappers are also supported to
  customize the observation and action spaces if it is in need.
* A new task can be enabled by a task definition file so that extending a new
  task is easy.
* Multiple sources are enabled to parse the task events from the operating
  system: screen text, screen icon, view hierarchy, and the system log, which
  makes Mobile-Env capable to adapt to most real-world apps without dedicated
  development. (Screen text and screen icon will be enabled with an external
  OCR tool and icon recognition tool. Currently, a wrapper of
  [EasyOCR](https://github.com/JaidedAI/EasyOCR) is integrated in the platform
  and can be enabled directly. An intergrated icon model will be embedded soon
  as well.)
* A brand-new tree-based event management system is designed to handle the
  logics of the task events. The details should be referred to the paper and
  the task definition guide. <!-- TODO: the paper link, the task definition
  guide -->

# Getting started

### Installation

<!-- TODO: pypi source -->

Clone the repository and build locally.

```sh
git clone https://github.com/deepmind/android_env/
cd android_env
pip install .
```

### Load and Run

Before loading the Mobile-Env environment, you will need to set up an Android
Emulator device. Then you can load the environment with some existing task
configs and start your experiments. A detailed guiding is provided in Training
and Evaluating Agents on Mobile-Env. <!-- TODO --> Several examples with a
random agent or a human agent is also provided under `examples`.

### Extend a new task

You may want to extend a new task for your experiments. First you need to
prepare an install package for your target app. Then you need to prepare a task
definition file written in the text format of ProtoBuf. The detail can be
sought in Extending a New App or a New Task Based on Mobile-Env. <!-- TODO -->
If your app relies on the dynamic Internet contents, a solution is provided in
Solution for Dynamic Information Apps. <!-- TODO -->

### Other Assistant Tools

We also developed an annotation tool for the human demonstrations, and a suite
of template tool to auto-generate task definitions according to templates and
to combine multiple task definitions to form a multi-step task. The details are
referred to Other Assistant Tools. <!-- TODO -->

## About

This library is developed and maintained by [SJTU
X-Lance](https://x-lance.sjtu.edu.cn/en). The corresponding paper is under
review of ACL Demo 2023. <!-- TODO: paper link -->

If you use Mobile-Env in your research, you can cite the project using the
following BibTeX:

```bibtex
@article{DanyangZhang2023_MobileEnv,
  title     = {{Mobile-Env}: A Universal Platform for Training and Evaluation of Mobile Interaction},
  author    = {Danyang Zhang and
               Lu Chen and
               Kai Yu},
  year      = {2023},
  %eprint    = {2105.13231},
  %archivePrefix = {arXiv},
  %primaryClass = {cs.LG},
  %volume    = {abs/2105.13231},
  url       = {https://github.com/X-LANCE/Mobile-Env},
}
```
