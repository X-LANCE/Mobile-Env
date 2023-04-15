<!-- vim: set nospell: -->
<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

0. 下载[安卓命令行工具](https://developer.android.com/studio)的压缩包，将之置于本文件夹下并重命名为`commandlinetools-linux-latest.zip`。

1. 构建docker1。

```sh
make docker1
```

2. 修改之并提交为新镜像。

```sh
docker run -it --device /dev/kvm my/mobile-env-web:0.5 /bin/bash
```

在容器内执行

```sh
mitmproxy # then press 'q' to exit
./setup_image.sh
exit
```

然后提交修改后的容器。

```sh
docker commit <container-id> my/mobile-env-web:0.6
```

3. 构建docker2。

```sh
make docker2
```
