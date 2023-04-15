<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

0. Download the package of [Android Commandline
   Tools](https://developer.android.com/studio) to this directory and rename it
   to `commandlinetools-linux-latest.zip`.

1. Build docker1.

```sh
make docker1
```

2. Modify and commit for a new image.

```sh
docker run -it --device /dev/kvm my/mobile-env-web:0.5 /bin/bash
```

Excecuate in the container:

```sh
mitmproxy # then press 'q' to exit
./setup_image.sh
exit
```

Then commit the modified container:

```sh
docker commit <container-id> my/mobile-env-web:0.6
```

3. Build docker2.

```sh
make docker2
```
