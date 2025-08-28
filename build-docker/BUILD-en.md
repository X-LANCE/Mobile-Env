<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```dockerfile', '```', 'dockerfile', 'NonText'): -->

0. Download the package of [Android Commandline
   Tools](https://developer.android.com/studio) to this directory and rename it
to `commandlinetools-linux-latest.zip`.

1. Create `proxy.dockerfile` under this directory. If no proxy is needed, you
   can just create an empty file. If proxy is needed, declare needed
environment variables in the following way:

```dockerfile
# HTTP proxy
ARG http_proxy=http://somewhere.xyz:port
ARG HTTP_PROXY=http://somewhere.xyz:port

# HTTPS proxy (the protocol may be either HTTP or HTTPS, depending on the proxy)
ARG https_proxy=http://somewhere.xyz:port
ARG HTTPS_PROXY=http://somewhere.xyz:port

# SOCKS5 proxy (if it is expected that DNS is also proxied，change socks5 to socks5h)
ARG all_proxy=socks5://somewhere.xyz:port
ARG ALL_PROXY=socks5://somewhere.xyz:port
```

2. [zpp](https://github.com/zdy023/z-nixtools/tree/master/toy-preprocessor) is
   used to preprocess dockerfiles in Makefile. You can also insert the contents
of `proxy.dockerfile` into the corresponding position in `Dockerfile` and save
it as `real.dockerfile` manually.

3. Create the image.

```sh
cd .. && make moobile-env
```
