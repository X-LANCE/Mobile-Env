<!-- vim: set nospell: -->
<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

0. 下载[安卓命令行工具](https://developer.android.com/studio)的压缩包，将之置于本文件夹下并重命名为`commandlinetools-linux-latest.zip`。下载[Frida服务端](https://github.com/frida/frida/releases)14.2.2版本的压缩文件，置之于本文件夹下。

1. 构建base镜像。

```sh
make base
```

2. 构建syscert半成品镜像。

```sh
make syscert
```

3. 修改之并提交为新镜像。

```sh
docker run -it --device /dev/kvm zdy023/mobile-env-rl:v2.1.a30_ga.syscert.m8.0.0.part /bin/bash
```

在容器内执行

```sh
mitmproxy # then press 'q' to exit
./setup_image.sh syscert
exit
```

然后提交修改后的容器。

```sh
docker commit <container-id> zdy023/mobile-env-rl:v2.1.a30_ga.syscert.m8.0.0
```

4. 构建frida半成品镜像。

```sh
make frida
```

5. 修改之并提交为新镜像。

```sh
docker run -it --device /dev/kvm zdy023/mobile-env-rl:v2.1.a30_ga.frida.f14.2.2.part /bin/bash
```

在容器内执行

```sh
./setup_image.sh frida
exit
```

然后提交修改后的容器。

```sh
docker commit <container-id> zdy023/mobile-env-rl:v2.1.a30_ga.frida.f14.2.2
```
