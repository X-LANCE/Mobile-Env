<!-- vim: set nospell: -->
<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```ebnf', '```', 'ebnf', 'NonText'): -->

## 其他辅助工具

### 人类演示标注工具

为了方便为行为克隆方法收集人类演示数据，开发了一款基于网页界面的标注工具。~~该标注工具可直接通过docker部署，其镜像现托管于[DockerHub](https://hub.docker.com/r/zdy023/mobile-env-web)（过时）。~~本平台的[演示视频](https://youtu.be/gKV6KZYwxGY)中，展示了如何使用该标注工具。

![标注工具1](images/annotation-tool-1.png)
![标注工具2](images/annotation-tool-2.png)
![标注工具3](images/annotation-tool-3.png)
![标注工具4](images/annotation-tool-4.png)

标注工具网页界面使用的方式请参见[README.md](../tools/annotation-tool/README-zh.md)。

除了网页界面外，还提供了几个命令行工具用来对标注结果预处理、可视化。相关代码存放于`../tools/annotation-tool/pkl_tools`。

##### 标注转存工具

网页界面工具保存下来的标注，每条交互历程会保存为一个pickle文件，名为`标注者名.%d.pkl`，其中`%d`是历程的序号。转存工具会将各单独的历程汇总，按其任务目标分类转存。其调用格式为

```sh
python resave_pickles.py PKL_NAME:S:T DUMPDIR TASKFOLDER
```

+ `PKL_NAME` - 要转存的历程文件的路径的模式，如`web-dumps/zdy023.%d.pkl`
+ `S`、`T` - 历程序号的范围（包含端点），用来取代路径模式串中的`%d`
+ `DUMPDIR` - 转存得到的标注文件要存放的目录
+ `TASKFOLDER` - 存放任务定义文件的目录

转存后的格式为：

```
{
    "meta": {
        "otask_id": str # 任务定义文件中声明的任务编号
        "otask_name": str # 任务定义文件中声明的任务名
        "task_definition_id": str # 任务定义文件的主文件名
    }
    "trajectories": [
        {
            "task_id": str # 该字段仅在列表首元素中出现
            "task": str # 该字段仅在列表首元素中出现
            "observation": np.ndarray # 形状为(宽, 高, 3)，类型为float32，以RGB形式保存观测到的屏幕图像
            "view_hierarchy": Optional[str] # 保存XML格式的视图框架
            "orientation": np.int64 # 记录屏幕方向
            "action_type": np.int64 # 0、1、2、3，分别对应TOUCH、LIFT、REPEAT、TEXT；列表首元素中没有该字段
            "touch_position": np.ndarray # 形状为(2,)，类型为float32，归一化到了[0, 1]，列表首元素中没有该字段；仅动作类型为TOUCH的步骤有该字段
            "input_token": str # 列表首元素中没有该字段；仅动作类型为TEXT的步骤有该字段
            “reward": float # 列表首元素中没有该字段；回报为0的步骤可能没有该字段
            "instruction": List[str] # 列表首元素中没有该字段；仅在触发了指令事件的步骤会有该字段
        },
        ...
    ]
}
```

##### 可视化工具

转存后的标注文件，可以通过该可视化工具，转成标注了动作、回报、指令等信息的帧，方便检查。

```sh
python visualize_pickle.py PKL_NAME DUMPDIR
```

其中

* `PKL_NAME` - 要可视化的标注文件
* `DUMPDIR` - 要保存提出的帧的目录

标注文件中的每条历程会提出一组帧，存放于`DUMPDIR`下的一个子目录中。该命令会依次打印出各历程的帧保存的目录路径。事实上，每条历程保存的子目录会命名为`任务定义文件名:历程序号%历程数量#历程长度`。可以采用`python visualize_pickle.py --help`命令查看更多命令行选项。

得到帧后，可以利用ffmpeg等工具将其连接成视频。或利用提供的`make_video_from_pickle.sh`脚本，直接得到帧与视频：

```sh
./make_video_from_pickle.sh PKL_NAME DUMPDIR
```

##### 标注编辑工具

简单编辑转存后的标注文件的工具。

```sh
python edit_pickle.py PKL_NAME MODIFIERS TASK_DIFINITION_PATH
```

* `PKL_NAME` - 要编辑的文件，编辑后旧文件会命名为`PKL_NAME.old`，新文件则会命名为`PKL_NAME`
* `MODIFIERS` - 描述如何修改
* `TASK_DIFINITION_PATH` - 存放相关的任务定义文件的目录

其中`MODIFIERS`的语法定义为

```ebnf
modifiers = modifier { "," modifier } ;
modifier = index ":" name [ ":" param { ":" param } ] ;
```

如`2:delete:1:3,2:rewardize:3:-1`表示：

1. 先对第2条（序号从0开始）历程应用`delete`修改，将区间`[1, 3)`的步骤删去（序号从0开始）
2. 再对第2条历程应用`rewardize`修改，将第3步（应用过`delete`后的第3步，也就是最开始的第5步）记录的回报减去1。

该工具目前支持的修改符有（以下未将历程序号项`index`标出）：

+ `delete:start:end`，删去记录中`[start-end)`区间的步骤
+ `instructionize:step:instruction_idx`，给第`step`步设置指令；指令通过序号指定，序号从0起始；可供选择的指令读取自任务定义文件，任务定义文件中指令事件槽上的各事件，按定义顺序，可依次从其中的`transformation`字段读取一条指令；若指令序号为-1，则会删去原有的指令
+ `rewardize:step:reward_delta`，修改第`step`步的回报，指定的`reward_delta`为回报的更新量
+ `remove`，删去该历程

### 任务定义模板工具箱

任务定义模板工具箱，用来根据任务定义文件的模板大规模扩增任务。相关代码存放于`../tools/templates.toolkits`。

该模板工具箱支持通过模板来实例化任务定义文件，并支持将多个小任务定义串接成一个大的复杂的多步任务定义文件。要通过该模板工具箱生成任务定义，共需要准备三类文件：

1. `<step>.textproto.template`，小步任务定义的模板
2. `<step>-<stepname>.conf`，模板实例化的配置，用来实例化一小步任务的定义，实例化的小步任务称为“任务元”
3. `<taskname>.task`，组合多个任务元的配置，用来指定组合哪些任务元得到最终的多步任务定义

##### 任务定义模板的语法

任务定义模板文件`<step>.textproto.template`大体上可按照[任务定义文件](task-definition-zh.md#扩展新任务：任务定义文件)的格式来写，只需要为需要动态实例化的文本声明要填充的槽位即可。槽位声明遵从以下格式：

```ebnf
slot = "<" [ modifier { "," modifier } ":" ] identifier ">" ;
```

槽位声明由标识符与可选的修饰符构成：标识符的格式同Python变量名相同，其声明该槽位填充的文本要依据实例化配置中的哪一项，标识符相同的槽位在实例化时会读取相同的配置项；修饰符声明，实例化时需要对读入的配置值做哪些变换；声明了多个修饰符时，修饰符会从右到左依次作用于配置值。下面给出一些槽位的例子：

* `<name>`
* `<lower:name>`
* `<regex_esc,regex_list:keywords>`

槽位语法的具体定义可以查看[`syntax.ebnf`](../tools/templates.toolkits/syntax.ebnf)。

实例化模板的参数由`<step>-<stepname>.conf`配置文件提供。该配置文件名由两部分构成，`-`前的第一部分需要与要实例化的模板名相同；第二部分则是为该任务元实例指定一个唯一名称。配置文件中，每一行为模板中的一个标识符提供一个配置值。格式为

```
identifier: value
```

例如：

```
name: search-task
keywords: bake,lobster,tails
```

组合任务元的配置文件`<taskname>.task`，每行指定一个任务元配置的文件名，以及一个可选的组合选项，如：

```
search-lobster
access_author-Bob   sr
```

目前有两种组合选项：`s`和`r`。若指定了`s`选项，则组合该任务元时会在最终任务定义的任务载入操作（`setup_steps`）中追加该任务元的载入操作；若指定了`r`选项，则会类似地追加该任务元的重置操作（`reset_steps`）；若未指定任何组合选项，则不会加入该任务元的任何载入或重置操作，即，只保留前缀任务元已加入的那些操作。每个组合任务的首个任务元的载入与重置操作都会默认保留在最终的组合任务中。各任务元会在实例化时按声明顺序组合，成为最终的大的多步任务中的小步骤。

##### 修饰符语法

实例化时，每个标识符对应的配置值可以按两种方式解释：

+ 单个字符串
+ `,`分隔的字符串列表

修饰符默认会将配置值作为单个完整的字符串处理；但若在修饰符末尾加上`'`，则该修饰符会将配置值视作列表，并分别作用于列表中各项上。如，对配置值`abc ,d ef, hi>g`，若直接应用修饰符`url_query`，则会得到`abc+%2Cd+ef%2C+hi%3Eg`；而若应用修饰符`url_query'`，则会得到`abc+,d+ef,+hi%3Eg`。

由于槽位取代的文本多用于textproto中的字符串中，因此实例化时，会默认转义输入的配置值中的`'`、`"`、`\`等字符；若不需要默认的转义，则可以在最后应用`no_quote`标识符关闭之。如，对配置值`abc ,d ef, hi>g`，若直接应用`to_list`，则会得到`[\"abc \", \"d ef\", \" hi>g\"]`；而若应用`no_quote,to_list`，则会得到`["abc ", "d ef", " hi>g"]`。

当前实现的通用修饰符大体可分为4类：

* 列表操作
  * `to_list` - 把输入的列表转为textproto的字符串列表
  * `regex_list` - 把输入的列表转为正则表达式中“或”连接的形式
* 正则操作
  * `regex_esc` - 按正则规则转义输入中的特殊字符
* 网址文本操作
  * `url_path` - 将输入视作网址中的路径（path）段来转义
  * `url_query` - 将输入视作HTTP地址中的请求（query）段来转义
  * `url_title` - 一般用于题目等类型的输入，用`-`替换掉其中的空格
* 一般文本操作
  * `lower` - 转为小写
  * `upper` - 转为大写

修饰符的具体定义、文档与实现参见[`modifiers.lhs`](../tools/templates.toolkits/modifiers-zh.lhs)、[`modifiers.py`](../tools/templates.toolkits/modifiers.py)。

##### 使用模板工具实例化任务定义

生成初始任务元配置：

```sh
python init_conf.py TEMPLATE STEPNAME DUMPDIR
```

指令参数：

* `TEMPLATE` - 模板文件的路径
* `STEPNAME` - 任务元配置文件名`<step>-<stepname>.conf`中的`stepname`部分
* `DUMPDIR` - 向那里输出配置文件的目录

执行后会在`DUMPDIR`下生成一份初始任务元配置文件。推荐采用这种方式初始化配置文件，因为可以有效防止自行编写时遗漏模板中出现的标识符。

实例化任务定义：

```sh
python parse.py --task TASKFILE -p TEMPLATES_DIR -o OUTPUTFILE
```

参数

* `TASKFILE` - 组合任务元的`.task`配置文件的路径，涉及的`.conf`文件应该与`.task`文件处在同一目录下。
* `TEMPLATES_DIR` - 需要的所有模板文件所在的目录
* `OUTPUTFILE` - 输出的任务定义文件的文件名
