<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

## Certificate Pinning Problem & Solutions

A huge amount of information apps provide varying contents from the Internet.
The transferred data are encrypted in SSL. Ussually, the app data can be
downloaded in advance and be replayed through an MitM proxy at runtime for
consistent evaluation and training. The MitM proxy can communicate with the app
only if the app trusts the certificate of the proxy. However, a policy named
*certificate pinning* are adopted by several apps so that these apps trust only
the certificates built in with the operating system (OS) image or the
certificate of the app's own server. For these apps, it will not work to simply
add the proxy's certificate into the user certificate list in the OS. As for
this problem, We tested three solutions.  This document will introduce the
solutions and present the corresponding config scripts.

The MitM proxy tested by us is [mitmproxy](https://mitmproxy.org/). The
solutions presented in the document are mainly derived from [Intercepting HTTPS
on Android](https://httptoolkit.com/blog/intercepting-android-https/). Besides,
there are several other references:

1. [Install System CA Certificate on Android
   Emulator](https://docs.mitmproxy.org/stable/howto-install-system-trusted-ca-android/)
2. [Intercepting HTTP(S) Traffic of Android
   Applications](https://kpj.github.io/misc/InterceptingHTTPTraffic.html)
3. [Defeating Android Certificate Pinning with
   Frida](https://httptoolkit.com/blog/frida-certificate-pinning/)
4. [Disable Certificate Verification on Android with
   Frida](https://www.gabriel.urdhr.fr/2021/03/17/frida-disable-certificate-check-on-android/)

#### Syscert Plan: Inject the Proxy Certificate into the Built-in Certificate Library of the OS

This plan is to bypass the certificate check of several apps with pinning by
injecting the proxy's certificate into the built-in certificate library of the
OS. To enable this solution, the root privillige is required on ADBD of the
Android virtual device (AVD). Thus, the image of Google APIs version is
supposed to be adopted rather than Google Play version. The `method` field of
`mitm_config` argument should be set to `syscert` while loading the
environment.

The certificate of the proxy should be injected into the used Android image
before loading Mobile-Env environment with this solution. A quick script
[`syscert_setup.exp`](../tools/syscert_setup.exp) is provided to complete this
config automatically. To run the script, a Tcl library
[expect](https://www.nist.gov/services-resources/software/expect) is needed.
Usually, you can intall it directly from the package repo of the Linux
distributions, *e.g.*,

```sh
apt install expect # Ubuntu
# pacman -S expect # ArchLinux
```

Then you can run the script to complete the config of the image:

```sh
tools/syscert_setup.exp [EMULATOR_PATH [AVD_NAME [CERT_PATH]]]
```

The three optional arguments are:

+ `EMULATOR_PATH` - The path to the executable of the emulator. Defaults to
  `$HOME/Android/Sdk/emulator`.
+ `AVD_NAME` - The name of the AVD (image) to be configured. Defaults to
  `Pixel_2_API_30_x64`.
+ `CERT_PATH` - The path to the SSL certificate to be injected. Defaults to
  `$HOME/.mitmproxy/mitmproxy-ca-cert.cer`.

#### Frida Plan: Replace the Certificate Verifier of the App at Runtime

This plan is to replace the app's certificate verifier by the runtime
instrument tool [Frida](https://github.com/frida/frida) to disable its pinning.
The root privillige is required on ADBD as well to apply this solution,
therefore, Google APIs image should be used. The `method` field of the
`mitm_config` argument should be set to `frida`. This solution is only tested
with frida 14.2.2 and the config script
[`frida_setup.sh`](../tools/frida_setup.sh) is provided for this version of
frida. Expect library is required for this script as well.

To enable this solution, the following items are required:

1. The frida server `frida-server` running on the AVD. You can download the
   correct version from the release page of Frida on GitHub.
2. The frida client `frida` running on the host machine. This software will be
   installed automatically by pip in the offered config script.
3. A JavaScript script for frida to replace the certificate verifiers. A valid
   script is provied by
   [httptoolkit/frida-android-unpinning](https://github.com/httptoolkit/frida-android-unpinning).

Run the script to complete the config of the image:

```sh
cd tools
./frida_setup.sh [EMULATOR_PATH [AVD_NAME [FRIDA_SERVER]]]
```

The three optional arguments are:

+ `EMULATOR_PATH` - The path to the executable of the emulator. Defaults to
  `$HOME/Android/Sdk/emulator`.
+ `AVD_NAME` - The name of the AVD (image) to be configured. Defaults to
  `Pixel_2_API_30_x64`.
+ `FRIDA_SERVER` - The path to the (compressed) program of the frida server.
  Defaults to `frida-server-14.2.2-android-x86_64.xz`.

#### Packpatch Plan: Re-package the App

According to [the Android development
document](https://developer.android.com/training/articles/security-config), the
apps can configure the behaviours of the certificate verifier in the standard
library including the validity and the domain range of pinning through a config
file. To disable the pinning for these apps, we can simply unpack the
installation package and modify its configs after decomplilation and re-pack it
to a new APK. The app installed by the new APK will not pin the SSL
certificates any more.

This solution can be conducted simply through
[apk-mitm](https://github.com/shroudedcode/apk-mitm) which automates the
process above.

apk-mitm will add a suffix `-patched` to the file name of the re-packed package
so that the novel file name will be `$package-patched.apk` if the original file
name is `$package.apk`. If the file name in the `install_apk` field is the
original `$package.apk` in the task definition file, this solution can be
enabled by setting the `method` field of the `mitm_config` argument to
`packpatch` during loading the environment. Then the platform will seek for the
re-packed package file automatically according to the suffix given for the
`patch-suffix` argument. Besides, the task set releaser may also directly give
the file name of the re-packed package in the task definition file and release
the re-packed installation package, in which case the platform user does not
need to specify the `mitm_config` parameter while loading the environment.
