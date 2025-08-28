<!-- vim: set nospell: -->
<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```dockerfile', '```', 'dockerfile', 'NonText'): -->

0. 下载[安卓命令行工具](https://developer.android.com/studio)的压缩包，将之置于本文件夹下并重命名为`commandlinetools-linux-latest.zip`。

1. 于本目录下创建`proxy.dockerfile`。若无需代理，可创建为空文件。若需要代理，可在其中按如下方式声明对应的环境变量

```dockerfile
# HTTP代理
ARG http_proxy=http://somewhere.xyz:port
ARG HTTP_PROXY=http://somewhere.xyz:port

# HTTPS代理（代理可能使用HTTP协议，也可能使用HTTPS协议）
ARG https_proxy=http://somewhere.xyz:port
ARG HTTPS_PROXY=http://somewhere.xyz:port

# SOCKS5代理（若需要SOCKS5一并代理域名解析，可将socks5更换为socks5h）
ARG all_proxy=socks5://somewhere.xyz:port
ARG ALL_PROXY=socks5://somewhere.xyz:port
```

2. Makefile中使用[zpp](https://github.com/zdy023/z-nixtools/tree/master/toy-preprocessor)完成预处理。也可手动将`proxy.dockerfile`中的内容插入`Dockerfile`中对应位置并另存为`real.dockerfile`。

3. 创建镜像

```sh
cd .. && make mobile-env
```
