<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vim: set nospell iminsert=2: -->

# 人类演示标注工具

### 构建前端

```sh
cd frontend
npm run build
```

### 构建后端

```sh
make backend
```

### 启动后端

```sh
python backend/server.py DUMPPATH TASK_DIFINITION_PATH
```

* `DUMPPATH` - pkl文件的路径，用来保存采集到的演示数据
* `TASK_DIFINITION_PATH` - 任务定义文件所在的目录

### 构建docker

请参照[BUILD.md](build-docker/BUILD-zh.md)。
