<!-- vim: set nospell iminsert=2: -->
<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

## 证书固定问题及解决方案

大量信息类应用依赖互联网获取变化的内容，其中大多都采用SSL加密传输应用数据。通常，这些应用数据可以预先下载下来，然后在运行时利用中间人代理工具回放之，以在测试、训练过程中保持一致。采用中间人代理工具为这类应用回放数据时，需要应用信任代理工具的证书，才能与之通信。然而有些应用采用了*固定证书*的策略，只信任操作系统内置证书库，或只信任本应用网站的证书，这时，简单地将代理证书加进操作系统的“用户证书”列表无法解决问题。对此，共测试了三种解决方案，本文档将介绍这些方案及平台对应提供的快捷脚本。

本平台测试的中间人代理工具为[mitmproxy](https://mitmproxy.org/)。本文档所采用的方案主要参考自[Intercepting HTTPS on Android](https://httptoolkit.com/blog/intercepting-android-https/)。其他参考文献包括：

1. [Install System CA Certificate on Android Emulator](https://docs.mitmproxy.org/stable/howto-install-system-trusted-ca-android/)
2. [Intercepting HTTP(S) Traffic of Android Applications](https://kpj.github.io/misc/InterceptingHTTPTraffic.html)
3. [Defeating Android Certificate Pinning with Frida](https://httptoolkit.com/blog/frida-certificate-pinning/)
4. [Disable Certificate Verification on Android with Frida](https://www.gabriel.urdhr.fr/2021/03/17/frida-disable-certificate-check-on-android/)

#### syscert方案：将代理证书注入操作系统内置证书库

该方案，通过将代理证书注入操作系统的内置证书库，来绕过部分固定证书的应用的检查。要启用该方案，需要安卓虚拟机上的ADBD能够获取root权限，因此，需要采用Google APIs版本的镜像，而非Google Play版本。在加载环境时，`mitm_config`参数中的`method`字段要设置为`syscert`。

使用该方案启动Mobile-Env环境时，需要事先将代理证书注入到使用的安卓镜像中，对此，平台提供了[`syscert_setup.exp`](../tools/syscert_setup.exp)脚本自动配置。该脚本需要安装Tcl库[expect](https://www.nist.gov/services-resources/software/expect)来运行，通常这可以直接从Linux发行版的软件仓库中安装，如

```sh
apt install expect # Ubuntu
# pacman -S expect # ArchLinux
```

运行该脚本，即可完成对镜像的配置：

```sh
tools/syscert_setup.exp [EMULATOR_PATH [AVD_NAME [CERT_PATH]]]
```

三个可选参数：

+ `EMULATOR_PATH` - 模拟器可执行文件的路径，默认为`$HOME/Android/Sdk/emulator`
+ `AVD_NAME` - 要修改的安卓虚拟机（镜像）名称，默认为`Pixel_2_API_30_x64`
+ `CERT_PATH` - 要注入的SSL证书的路径，默认为`$HOME/.mitmproxy/mitmproxy-ca-cert.cer`

#### frida方案：运行时替换应用程序的证书验证器

该方案，采用运行时注入工具[Frida](https://github.com/frida/frida)替换应用程序的证书验证器，以解除其固定证书。该方案同样需要adbd获取root权限，因此需要采用Google APIs版本的镜像。加载环境时，`mitm_config`参数中，`method`字段要设置为`frida`。本方案仅基于frida 14.2.2完成了测试，并针对该版本，提供了配置脚本[`frida_setup.sh`](../tools/frida_setup.sh)，该脚本同样需要安装expect来执行。

要采用本方案，需要准备

1. 运行在安卓虚拟机上的frida服务端`frida-server`。请从Frida的GitHub发布页下载需要的版本。
2. 运行在宿主机上的frida客户端`frida`。提供的配置脚本会自动利用pip工具安装。
3. frida用来替换证书验证器的JavaScript脚本。可以采用[httptoolkit/frida-android-unpinning](https://github.com/httptoolkit/frida-android-unpinning)仓库提供的脚本。

运行配置脚本，即可完成对镜像的配置：

```sh
cd tools
./frida_setup.sh [EMULATOR_PATH [AVD_NAME [FRIDA_SERVER]]]
```

三个可选参数：

+ `EMULATOR_PATH` - 模拟器可执行文件的路径，默认为`$HOME/Android/Sdk/emulator`
+ `AVD_NAME` - 要修改的安卓虚拟机（镜像）名称，默认为`Pixel_2_API_30_x64`
+ `FRIDA_SERVER` - frida服务端程序（的压缩文件）的路径，默认为`frida-server-14.2.2-android-x86_64.xz`

#### packpatch方案：重打包应用程序

根据[Android开发文档](https://developer.android.com/training/articles/security-config)，采用标准库证书验证器的应用程序可以通过配置文件配置验证器的行为，包括固定证书与否以及限制的域名范围等。因此，对这类应用，可以将安装包解包、反编译后，修改其配置文件，再重新编译打包得到新的APK安装包。使用得到的新安装包安装上的应用程序就不会再固定SSL证书了。

[apk-mitm](https://github.com/shroudedcode/apk-mitm)工具将该过程自动化了，可以直接通过该工具将目标应用重打包。

若采用apk-mitm重打包应用包，应用包文件原名为`$package.apk`，则打包后的文件名，apk-mitm默认会给主文件名添加后缀`-patched`，变为`$package-patched.apk`。若提供的任务定义文件中，`install_apk`字段提供的文件名是原文件名`$package.apk`，则可以在加载环境时，可将`mitm_config`参数的`method`字段设置为`packpatch`，此时平台就会根据`patch-suffix`参数指定的后缀自动寻找重打包过的安装包；任务集发布者也可以直接在任务定义文件中指定重打包后的文件名，并发布重打包后的安装包，此时平台使用者加载平台时就不需要再指定`mitm_config`参数了。
