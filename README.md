<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```bibtex', '```', 'bib', 'NonText'): -->

## NEWS!!

* (2025-09-02 v4.2)
  * Updated some interfaces for `android_env.interfaces.env.Environment`
  * Added cleaning mechanism for cached `TaskManager`s to save runtime resources
  * Added support of manual simulator restart at environment reset
  * Fixed other bugs
  * Building new Docker image

See our [Change log](Changelog) for details.

* (2024-12-18 v4.1) Some essential bugs are fixed. See [Change log](Changelog)
  for details.

* (2024-07-14 v4.0)
  * Added new action and observation type of ADB
  * Enabled input of common UTF-8 strings for `TEXT` action
  * Enabled fuzzy match method for screen text events. Enabled triggering
    threshold for fuzzy match modes.
  * Migrated from `dm_env` to `android_env.interfaces` to distinguish
    successful, failed, and truncated episode ends. Updated episode end events
    to control its triggering in the task definition file more conviniently.
  * Added `cache_until` field for event slots to correctly trigger an `AND`
    node whose sub-events are expected to be triggered simultaneously.  Now an
    activatated event can be cached temporarily until another triggered event
    clears it.
  * Added `null_listener` for target-less event nodes.
  * Applied image compression in `RemoteSimulator`.
  * Migrated from `gym` to `gymnasium`.
  * Updates to `VhIoWrapper` and `TapActionWrapper`
  * Minor updates to annotation tool.

See our [Change Log](Changelog) for details. The documents will be revised
soon. A new tutorial w.r.t. episode event management is on plan.

* (2024-04-30 v3.6)
  * Updated function to load a remote simulator to enable providing the remote
    resources with a different path with the path of the local task definition
    file.
  * Updated task template toolkit, added new slot modifiers and sytaxes for
    task config file.
  * Fixed known bugs.

* (2023-12-18 v3.5)
  * Owing to the long time delay of VH check and screenshot check, we updated
    the mechanism of managing the check time. By this way, the requirement of
    sufficient check for the episode events and the resulted long delay can be
    balanced.
  * Added multiple rating methods to `ResponseEvent`: regex matching, fuzzy
    matching, and vector encoding matching.
  * Improved `VhIoWrapper` and `TapActionWrapper`. Added support to `SCROLL`
    and `TYPE` to `TapActionWrapper`.
  * Optimized `RemoteSimulator`. In order to reduce the delay of network
    transfering, enabled action batch to send and execute a group of actions
    and enabled resizing the image before and after transferring to shrink the
    transferred data.
  * Merged annotation tool to the main branch. The original annotation-tool
    branch is deprecated.
  * Added support to `ResponseEvent` to annotation tool.
  * Supplemented several commandline options to annotation-tool.

For more details, please see our [Change Log](Changelog) and Documents.

* (2023-10-31 v3.0) Migrated VH node specification from the original VH path to
  Mobile-Env-customized CSS selector (me-selector) and added repeatability
  control to EventSlots. Repeatability control for EventSlots may be useful to
  prevent repetitive triggering of an `OR`-type virtual event combining
  multiple types of event sources.

Please see our [Change Log](Changelog) and
[Document](docs/task-definition-en.md).

* (2023-09-21 v2.1) Added *REMOTE SIMULATOR* to solve the problem that
  hardware-based acceleration for virtualization is not enabled on many GPU
  clusters

Please see our [Change Log](Changelog) and [Document](docs/env-usage-en.md).

* (2023-06-30 v2.0) New type of event "response to human user" (RHU,
  `ResponseEvent`). Now enables the agent to generate response to human user
  and parses episode signales from it. This will enable interaction tasks like
  question-answering, retrieval, *etc*.

Please see our [Change Log](Changelog), [Usage Document](docs/env-usage-en.md),
and [Task Definition Document](docs/task-definition-en.md).

# Mobile-Env: Building Qualified Evaluation Benchmarks for GUI Interaction

Mobile-Env is a interaction platform for building evaluation benchmarks for GUI
interaction and evaluating and training GUI agents.  Our paper is available at
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

## Getting Started

### Installation

~~Install from PyPI:~~

```sh
#pip insall mobile-env-rl
```

~~or clone the repository and build locally.~~

Clone the repository and build locally (the proto files need to be compiled
locally).

```sh
git clone https://github.com/X-LANCE/Mobile-Env
cd Mobile-Env
pip install .
```

~~Several [Docker images](https://hub.docker.com/r/zdy023/mobile-env-rl) with
well-configured Android AVD are also available.~~

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

Several demo task definitions are provided under `demos`. Three of them are
migrated from  AndroidEnv:

* `classic_2048.m.textproto` - [Classic 2048
  game](https://github.com/google-deepmind/android_env/blob/main/docs/example_tasks.md#classic-2048).
* `accessibility_forwarder_clock_set_timer.m.textproto` - A simple task
  requiring the agent to [reset a running
  timer](https://github.com/google-deepmind/android_env/blob/main/docs/example_tasks.md#accessibility-forwarder).
* `systemui_egg_land_default.m.textproto` - [Flappy
  Droid](https://github.com/google-deepmind/android_env/blob/main/docs/example_tasks.md#flappydroid).
  An open-sourced implementation of classic game, Flappy Bird.

Another one, `openmoneybox.add_billings.textproto` is defined upon an
open-sourced billing app,
[OpenMoneyBox](https://f-droid.org/en/packages/com.igisw.openmoneybox/).
Details are referred to in the task definition files.

### Miscellaneous Auxiliary Tools

We also developed an annotation tool for the human demonstrations, and a suite
of template tool to auto-generate task definitions according to templates and
to combine multiple task definitions to form a multi-step task. The details are
referred to in [Miscellaneous Auxiliary Tools](docs/other-tools-en.md).

### Reference Time-Consuming and Memory Usage o Mobile-Env

The data are measured under the configuration below:

* OS and hardware:
  * Operating System: Manjaro 23.1.0 Vulcan
  * Kernel Version: x86\_64 Linux 6.1.64-1-MANJARO
  * CPU: Intel Core i7-10700 @ 16x 4.8GHz
  * GPU: NVIDIA GeForce RTX 3090
  * RAM: 64 GB
  * KVM acceleration enabled
* Android development tools
  * Android emulator version 32.1.14.0
  * Android platform tools 34.0.4
  * libvert 1:9.9.0
* Python & packages
  * Python 3.8.16
  * EasyOCR 1.7.2
  * sentence-transformers 2.2.2
* Android Virtual Device
  * Device type: Pixel 2
  * API version: API 30
  * OS Variant: Google APIs
  * CPU cores: 4
  * Memory: 8 GB
  * Screen size: 1080×1920

|                           Item                          |     Avg Time     |    Time Std Dev   |
|:-------------------------------------------------------:|:----------------:|:-----------------:|
|                      `TOUCH` action                     |     410.50 µs    |      64.71 µs     |
|                      `LIFT` action                      |     412.30 µs    |      84.18 µs     |
|                      `TEXT` action                      | ~~1.30 s~~ 0.58s | ~~0.28 s~~ 0.03 s |
|                   screenshot capturing                  |     19.94 ms     |      21.47 ms     |
| invocation of Sentence Transformer（all-MiniLM-L12-v2） |      8.51 ms     |      0.17 ms      |
|                       VH capturing                      |      2.53 s      |       1.90 s      |
|                  invocation of EasyOCR                  |      0.44 s      |       0.08 s      |

When only an [app of WikiHow
2.9.6](https://apkcombo.com/zh/wikihow-how-to-do-anything/com.wikihow.wikihowapp/download/apk)
is running, the Android emulator occupies 6,031 MiB of virtual memory and 3,444
MiB of residual memory.

## About

This library is developed and maintained by [SJTU
X-Lance](https://x-lance.sjtu.edu.cn/en). The corresponding paper is available
at <https://arxiv.org/abs/2305.08144>.

If you find Mobile-Env useful in your research, you can cite the project using
the following BibTeX:

```bibtex
@article{DanyangZhang2023_MobileEnv,
  title     = {{Mobile-Env}: Building Qualified Evaluation Benchmarks for LLM-GUI Interaction},
  author    = {Danyang Zhang and
               Zhennan Shen and
               Rui Xie and
               Situo Zhang and
               Tianbao Xie and
               Zihan Zhao and
               Siyuan Chen and
               Lu Chen and
               Hongshen Xu and
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
