<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

0. Download the package of [Android Commandline
   Tools](https://developer.android.com/studio) to this directory and rename it
   to `commandlinetools-linux-latest.zip`. Download version 14.2.2 of the
   compressed client program of [Frida
   server](https://github.com/frida/frida/releases) to this directory.

1. Build `base` image.

```sh
make base
```

2. Build the partial version of `syscert` image.

```sh
make syscert
```

3. Modify and commit for a new image.

```sh
docker run -it --device /dev/kvm zdy023/mobile-env-rl:v2.1.a30_ga.syscert.m8.0.0.part /bin/bash
```

Execute in the container:

```sh
mitmproxy # then press 'q' to exit
./setup_image.sh syscert
exit
```

Then commit the modified container:

```sh
docker commit <container-id> zdy023/mobile-env-rl:v2.1.a30_ga.syscert.m8.0.0
```
4. Build the partial version of `frida` image.

```sh
make frida
```

5. Modify and commit for a new image.

```sh
docker run -it --device /dev/kvm zdy023/mobile-env-rl:v2.1.a30_ga.frida.f14.2.2.part /bin/bash
```

Execute in the container:

```sh
./setup_image.sh frida
exit
```

Then commit the modified container:

```sh
docker commit <container-id> zdy023/mobile-env-rl:v2.1.a30_ga.frida.f14.2.2
```
