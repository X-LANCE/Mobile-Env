<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```bibtex', '```', 'bib', 'NonText'): -->
<!-- vim: set nospell iminsert=2: -->

## 最近更新

* （2024-07-14 v4.0）
  * 新增了ADB动作和观测类型
  * 现已支持在`TEXT`动作中输入一般UTF-8字符串
  * 为屏幕文本事件添加了对模糊文本识别的支持；为各采用模糊文本识别的事件添加了触发阈值功能
  * 将接口从`dm_env`迁移到了`android_env.interfaces`上，以区分成功、失败、中止三种历程结束状态。更新了历程结束事件，现在能够更方便地在任务定义文件中控制事件的触发
  * 为各事件槽添加了`cache_until`字段，现在可以通过该字段将一事件的触发状态缓存，直至另一事件触发后清除它。这能够保证`AND`节点的子事件同时达到触发状态，从而正确激活`AND`事件
  * 新添了`null_listener`，来放置不直接连接到某实在历程事件（得分、回报、历程结束、过程中指令、额外信息等）的事件节点
  * 在`RemoteSimulator`中启用了图片压缩算法
  * 从`gym`迁移到了`gymnasium`
  * 更新了`VhIoWrapper`和`TapActionWrapper`
  * 对标注工具有些小更新

详情请查看[更新日志](Changelog)。相关文档不日将会更新。新计划编写一册新教程指导如何管理历程事件，敬请期待。

* （2024-04-30 v3.6）
  * 更新了加载远程模拟器的函数，用以为远程资源提供不同于本地任务定义文件所在目录的路径
  * 更新了任务模板工具，增加了新的槽位修饰符与任务配置文件语法
  * 修复了已知的问题

具体信息请查看[更新日志](Changelog)和相关文档。

* （2023-12-18 v3.5）
  * 由于检查视图框架和屏幕图像耗时较长，因此更新了机制来更灵活地管理在什么时机检查视图框架与屏幕图像，以平衡对历程事件的充分检查的需求和所带来交互时延升高
  * 为`ResponseEvent`（回复事件）添加了多种评分方式：正则匹配、模糊匹配、向量编码匹配
  * 优化了`VhIoWrapper`、`TapActionWrapper`，为`TapActionWrapper`添加了对`SCROLL`、`TYPE`动作的支持
  * 优化了远程模拟器，为缓解网络传输的时延问题，支持了一次性发送、执行一个动作组，支持了在传输前后对屏幕图像缩放以减少传输的数据量
  * 将标注工具合并到了主分支，原标注工具分支已废弃
  * 为标注工具添加了对回复事件的支持
  * 为标注工具新添了一些命令行选项

具体信息请查看[更新日志](Changelog)和相关文档。

* （2023-10-31 v3.0）将指定视图框架节点的方式，从原本的“视图框架路径”改为了Mobile-Env定制的CSS选择器（me-selector），并为EventSlot节点也添加了可重复性控制功能。控制EventSlot的可重复性会有助于避免重复触发那种结合了多类事件源的`OR`型虚拟事件

具体信息请查看[更新日志](Changelog)和[文档](docs/task-definition-zh.md)。

* （2023-09-21 v2.1）增加了“远程模拟器”，用以应对许多显卡集群上未启用对虚拟化的硬件加速的问题

具体信息请查看[更新日志](Changelog)和[文档](docs/env-usage-zh.md)。

* （2023-06-30 v2.0）增加了新事件类型“给人类用户的回复”（`ResponseEvent`），允许智能体给人类用户产生回复，并从中解析历程信号，用来支持问答、检索类型的交互任务

具体信息请查看[更新日志](Changelog)、[使用文档](docs/env-usage-zh.md)、[任务定义文档](docs/task-definition-zh.md)。

# Mobile-Env：构建合格的图形界面交互基准

Mobile-Env是用于构建图形界面交互评测基准，评测、训练图形界面交互智能体的交互平台，论文现公开于[arXiv](https://arxiv.org/abs/2305.08144)。

Mobile-Env基于[AndroidEnv](https://github.com/deepmind/android_env)开发。通过Mobile-Env，智能体可以观测到Android操作系统的屏幕截图和视图框架（View Hierarchy，由于获取时延较高，该项是默认关闭的），然后采取点触屏幕或输入词元（token）等动作来与Android应用交互。交互过程中的某些步骤上，步骤指令、回报、历程结束等历程信号可能触发并统治智能体。具体是哪些步骤取决于特定的[任务定义](docs/task-definition-zh.md)，可能是打开了某个目标界面，或者滚动到了正确的区域等等。

所构建的WikiHow任务集发布于[Hugging Face平台](https://huggingface.co/datasets/zdy023/WikiHow-taskset)。

* [英文文档（Documents in English）](README.md)

## 目录

* [利用Mobile-Env验证、训练智能体](docs/env-usage-zh.md)
* [基于Mobile-Env扩展新环境（手机应用）或新任务](docs/task-definition-zh.md)
* [证书固定问题及解决方案](docs/dynamic-app-zh.md)
* [其他辅助工具](docs/other-tools-zh.md)

## 平台特点

作为信息界面交互平台，Mobile-Env灵活，适用性强，易于扩展。其具有以下特点：

* 观测空间包含屏幕截图和视图框架，动作空间包括点触与输入词元，同时还可以通过各种包装器修改观测与动作空间的形式，因此，各种智能体，无论是基于视觉观测的还是基于文本观测，动作空间无论是连续的还是离散的，都可以利用Mobile-Env来评测。
* 新任务通过任务定义文件可以很容易地扩展。
* Mobile-Env能够从多种操作系统反馈中解析任务事件，包括：屏幕文本、屏幕图标、视图框架、系统日志。因此Mobile-Env能够直接迁移到大多现实应用上，而不需要对应用定制修改。（屏幕文本和屏幕图标需要外部的文字、图标识别工具来支持。目前平台内置了一个对[EasyOCR](https://github.com/JaidedAI/EasyOCR)的包装，可以直接启用。内置的图标模型也在训练调试中，会在将来集成进去。）

## 快捷指南

### 安装

从PyPI安装：

```sh
pip install mobile-env-rl
```

或克隆本仓库并在本地构建：

```sh
git clone https://github.com/X-LANCE/Mobile-Env
cd Mobile-Env
pip install .
```

此外，也提供了部分带有已配置好的安卓镜像的[Docker镜像](https://hub.docker.com/r/zdy023/mobile-env-rl)。

### 加载、运行Mobile-Env以评测或训练

加载Mobile-Env的环境前，需要先创建一个[安卓模拟器](https://developer.android.com/about)虚拟设备。然后才能加载已有的任务定义并启动环境。详细的指南请参考[利用Mobile-Env验证、训练智能体](docs/env-usage-zh.md)。`examples`目录下提供了几个采用随机智能体，或由人类充当智能体的示例程序。

### 扩展新环境、新任务

要为Mobile-Env扩展新环境，需要准备好应用安装包，并确保其能在某个版本的安卓模拟器上启动、运行。如果该应用需要一些变化的在线数据，那么还需要将必要的数据保存下来，并在使用中回放，以保证评测的一致。这种情况下，还需要确认这些[解除证书固定的方法](docs/dynamic-app-zh.md)对该应用有效。至于扩展新任务，则只需要准备好任务定义文件。具体的教程，请参考[基于Mobile-Env扩展新环境（手机应用）或新任务](docs/task-definition-zh.md)。

`demos`目录下提供了几个示例任务定义。其中三个迁移自AndroidEnv：

* `classic_2048.m.textproto` - [经典的2048小游戏](https://github.com/google-deepmind/android_env/blob/main/docs/example_tasks.md#classic-2048)
* `accessibility_forwarder_clock_set_timer.m.textproto` - 简单的小任务，需要智能体按按钮[重设计时器](https://github.com/google-deepmind/android_env/blob/main/docs/example_tasks.md#accessibility-forwarder)
* `systemui_egg_land_default.m.textproto` - [Flappy Droid](https://github.com/google-deepmind/android_env/blob/main/docs/example_tasks.md#flappydroid)，对经典小游戏Flappy Bird的开源复现

剩下一个文件`openmoneybox.add_billings.textproto`，基于开源记账应用[OpenMoneyBox](https://f-droid.org/en/packages/com.igisw.openmoneybox/)定义。任务的具体内容请查看该任务定义文件。

### 其他辅助工具

还开发了一套标注工具用于采集人类演示，以及一套模板工具，来根据模板生成任务定义，并将多个任务定义串接成一个多步任务。更详细的介绍请查看[其他辅助工具](docs/other-tools-zh.md)。

### Mobile-Env执行的开销参考

以下数据测量自如下配置：

* 操作系统与硬件：
  * 操作系统：Manjaro 23.1.0 Vulcan
  * 内核版本：x86\_64 Linux 6.1.64-1-MANJARO
  * 处理器：Intel Core i7-10700 @ 16x 4.8GHz
  * 显卡：NVIDIA GeForce RTX 3090
  * 运存：64GB
  * 启用内核虚拟化硬件加速
* 安卓开发工具
  * Android emulator version 32.1.14.0
  * Android平台工具34.0.4
  * libvert 1:9.9.0
* Python及相关包
  * Python 3.8.16
  * EasyOCR 1.7.2
  * sentence-transformers 2.2.2
* 安卓虚拟机
  * 机型：Pixel 2
  * 接口版本：API 30
  * 系统变种：Google APIs
  * 处理器核数：4
  * 存储：8GB
  * 屏幕尺寸：1080×1920

|                      项目                     |     耗时均值    |    耗时标准差   |
|:---------------------------------------------:|:---------------:|:---------------:|
|                  `TOUCH`动作                  |     410.50µs    |     64.71µs     |
|                   `LIFT`动作                  |     412.30µs    |     84.18µs     |
|                   `TEXT`动作                  | ~~1.30s~~ 0.58s | ~~0.28s~~ 0.03s |
|                      截图                     |     19.94ms     |     21.47ms     |
| 调用Sentence Transformer（all-MiniLM-L12-v2） |      8.51ms     |      0.17ms     |
|                  获取视图框架                 |      2.53s      |      1.90s      |
|                  调用EasyOCR                  |      0.44s      |      0.08s      |

单运行一个[WikiHow 2.9.6应用](https://apkcombo.com/zh/wikihow-how-to-do-anything/com.wikihow.wikihowapp/download/apk)时，占用虚拟内存6031MiB，残存内存3444MiB。

## 项目信息

本库由[上海交通大学跨媒体语言智能实验室](https://x-lance.sjtu.edu.cn/en)（X-Lance）开发、维护。相关论文可查阅<https://arxiv.org/abs/2305.08144>。

若Mobile-Env对您的研究起到了帮助，敬请引用本项目。可以使用下列的BibTex：

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
```
