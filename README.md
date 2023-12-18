<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```bibtex', '```', 'bib', 'NonText'): -->

WARNING! This branch is obsolete. The development is merged into the main
branch.

# Mobile-Env: An Evaluation Platform and Benchmark for Interactive Agents in LLM Era 

Mobile-Env is a interaction platform for evaluation and training of the
interaction of information user interface (InfoUI). Our paper is available at
[arXiv](https://arxiv.org/abs/2305.08144).

Mobile-Env is developed based on
[AndroidEnv](https://github.com/deepmind/android_env). The agent can take the
screenshot and the view hierarchy (disabled defaultly for the long latency) as
the observation and take a touch or type a token as the action to interact with
the Android apps. Several episode signals like step instructions, rewards, or
the episode end will be informed during interaction at some crucial steps. A
so-called crucial step may be opening a target page, srolling to a correct
area, *etc*. and is depending on the specific [task
definition](docs/task-definition-en.md).

The proposed WikiHow task set is available at the [Hugging Face
Platform](https://huggingface.co/datasets/zdy023/WikiHow-taskset).

* [Documents in Chinese (中文文档)](README-zh.md)

## Index

* [Evaluating and Training Agents on Mobile-Env](docs/env-usage-en.md)
* [Extending a New Environment (App) or a New Task Based on
  Mobile-Env](docs/task-definition-en.md)
* [Certificate Pinning Problem & Solutions](docs/dynamic-app-en.md)
* [Miscellaneous Auxiliary Tools](docs/other-tools-en.md)

## Platform Features

Mobile-Env is a flexible, adaptable, and easily-extendable platform for InfoUI
interaction with the following features:

* Both screenshot and view hierarchy are provided as the observation. The touch
  and token typing are provided as the action. Wrappers are also supported to
  customize the observation and action spaces. Thus, both visual-based and
  text-based agents, both agents with continuous action space and discrete
  action space, can be evaluated on Mobile-Env.
* New tasks can be easily extended through task definition files.
* Multiple sources are enabled to parse the task events from the operating
  system: screen text, screen icon, view hierarchy, and the system log, which
  makes Mobile-Env capable of adapting to most real-world apps without
  dedicated development. (Screen text and screen icon will be enabled with an
  external OCR tool and icon recognition tool. Currently, a wrapper of
  [EasyOCR](https://github.com/JaidedAI/EasyOCR) is integrated in the platform
  and can be enabled directly. An intergrated icon model will be embedded soon
  as well.)

# Getting Started

### Installation

<!-- TODO: pypi source -->

Clone the repository and build locally.

```sh
git clone https://github.com/deepmind/android_env/
cd android_env
pip install .
```

### Load and Run Mobile-Env for Evaluation or Training

Before loading the Mobile-Env environment, you will need to set up an [Android
Emulator](https://developer.android.com/about) device. Then you can load the
environment with some existing task definitions and start your experiments. A
detailed guidance is provided in [Evaluating and Traning Agents on
Mobile-Env](docs/env-usage-en.md). Several examples with a random agent or a
human agent is also provided under `examples`.

### Extend a New Environment or a New Task

To extend a new environment for Mobile-Env, the environment designer needs to
prepare the app package and ensure that the package manages to launch and run
on some versions of Android Emulator. If the app requires varying online data,
the necessary data should be crawled and dumped and then be replayed for a
consistent evaluation. In such case, the designer is supposed to validate the
certain effectiveness of [certificate unpinning plan](docs/dynamic-app-en.md)
for the package.  As regards to extend new tasks, task definition files are
just required. Detailed instructions can be found in [Extending a New
Environment (App) or a New Task Based on
Mobile-Env](docs/task-definition-en.md).

### Miscellaneous Auxiliary Tools

We also developed an annotation tool for the human demonstrations, and a suite
of template tool to auto-generate task definitions according to templates and
to combine multiple task definitions to form a multi-step task. The details are
referred to in [Miscellaneous Auxiliary Tools](docs/other-tools-en.md).

## About

This library is developed and maintained by [SJTU
X-Lance](https://x-lance.sjtu.edu.cn/en). The corresponding paper is available
at <https://arxiv.org/abs/2305.08144>.

If you find Mobile-Env useful in your research, you can cite the project using
the following BibTeX:

```bibtex
@article{DanyangZhang2023_MobileEnv,
  title     = {{Mobile-Env}: An Evaluation Platform and Benchmark for Interactive Agents in LLM Era},
  author    = {Danyang Zhang and
               Lu Chen and
               Zihan Zhao and
               Ruisheng Cao and
               Kai Yu},
  journal   = {CoRR},
  volume    = {abs/2305.08144},
  year      = {2023},
  url       = {https://arxiv.org/abs/2305.08144},
  eprinttype = {arXiv},
  eprint    = {2305.08144},
}
```
