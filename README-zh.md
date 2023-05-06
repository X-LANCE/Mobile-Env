<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```bibtex', '```', 'bib', 'NonText'): -->
<!-- vim: set nospell iminsert=2: -->

# Mobile-Env：通用的手机交互训练与验证的平台

Mobile-Env是针对信息用户界面交互设计的新的训练、验证平台。所谓信息用户界面，其包含丰富的文本内容，同时交错有各类多媒体内容，这些不同模态的内容都按照一定空间结构，以不同的样式渲染在同一界面上。这种形式显著不同于具身智能、视频游戏、文字游戏等已有控制问题中的交互环境。Mobile-Env的演示视频可在<https://youtu.be/gKV6KZYwxGY>观看。

Mobile-Env是基于[AndroidEnv](https://github.com/deepmind/android_env)开发的。通过Mobile-Env，智能体可以观测到Android操作系统的屏幕截图和视图框架（View Hierarchy，由于获取时延较高，该项是默认关闭的），然后采取点触屏幕或输入词元（token）等动作来与Android应用交互。交互过程中的某些步骤上，回报、步骤指令、交互终结等任务事件可能触发并统治智能体。具体是哪些步骤取决于特定的[任务定义](docs/task-definition-zh.md)，可能是打开了某个目标界面，或者滚动到了正确的区域等等。

所构建的WikiHow任务集发布于[Hugging Face平台](https://huggingface.co/datasets/zdy023/WikiHow-taskset)。

* [英文文档（Documents in English）](README.md)

## 目录

* [利用Mobile-Env训练、验证智能体](docs/env-usage-zh.md)
* [基于Mobile-Env扩展新的应用程序或新任务](docs/task-definition-zh.md)
* [针对动态信息的应用的解决方案](docs/dynamic-app-zh.md)
* [其他辅助工具](docs/other-tools-zh.md)

## 平台特点

作为信息界面交互平台，Mobile-Env灵活，适用性强，易于扩展。其具有以下特点：

* 观测空间包含屏幕截图和视图框架，动作空间包括点触与输入词元，适用于各种手机应用。同时支持通过环境包装器修改观测与动作空间的形式。
* 新任务可以通过任务定义文件简单启用，因此扩展新任务非常容易。
* Mobile-Env能够从多种操作系统反馈中解析任务事件，包括：屏幕文本、屏幕图标、视图框架、系统日志。因此Mobile-Env能够直接迁移到大多现实应用上，而不需要对应用定制修改。（屏幕文本和屏幕图标需要外部的文字、图标识别工具来支持。目前平台内置了一个对[EasyOCR](https://github.com/JaidedAI/EasyOCR)的包装，可以直接启用。内置的图标模型也在训练调试中，会在将来集成进去。）
* 设计了一套崭新的树状事件管理系统来处理任务事件逻辑。具体介绍可以查看论文和[任务定义指南](docs/task-definition-zh.md)。<!-- TODO: 论文链接 -->

## 快捷指南

### 安装

<!-- TODO: pypi源 -->

克隆本仓库并在本地构建。

```sh
git clone https://github.com/deepmind/android_env/
cd android_env
pip install .
```

### 加载、运行

接载Mobile-Env的环境前，需要先创建一个[安卓模拟器](https://developer.android.com/about)虚拟设备。然后才能加载已有的任务配置并启动环境。详细的指南请参考[利用Mobile-Env训练、验证智能体](docs/env-usage-zh.md)。`examples`目录下提供了几个采用随机智能体，或由人类充当智能体的示例程序。

### 扩展新任务

如果实验需要扩展一些新任务，首先要为要使用的应用程序把安装包准备好，然后需要编写ProtoBuf文本格式的任务定义文件。详细说明请查看[基于Mobile-Env扩展新的应用程序或新任务](docs/task-definition-zh.md)。如果应用依赖互联网上的动态内容，请参考[针对动态信息的应用的解决方案](docs/dynamic-app-zh.md)解决。

### 其他辅助工具

还开发了一套标注工具用于采集人类演示，以及一套模板工具，来根据模板生成任务定义，并将多个任务定义串接成一个多步任务。更详细的介绍请查看[其他辅助工具](docs/other-tools-zh.md)。

## 项目信息

本库由[上海交通大学跨媒体语言智能实验室](https://x-lance.sjtu.edu.cn/en)（X-Lance）开发、维护。相关论文已投稿ACL Demo 2023，正在审稿中。<!-- TODO: 论文链接 -->

若在研究中使用了Mobile-Env，敬请引用本项目。可以使用下列的BibTex：

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
