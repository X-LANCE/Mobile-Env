<!-- vimc: call SyntaxRange#Include('```ebnf', '```', 'ebnf', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```proto', '```', 'proto', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

## Extending a New App or a New Task Based on Mobile-Env

To extend a new task for the Mobile-Env platform, you need to prepare:

+ The installation package of the corresponding Android app
+ The external data, *e.g.*, the crawled online data
+ The definition of the task meta-information in textproto format, including
  the task id, the description, the setup steps, the task events, *etc.*

### Preparation of the App Package

You need to prepare the installation package for the app and check if it can be
successfully launched and run on the emulator. Nowadays, most desktops have an
`amd64` CPU, however, most Android mobiles run on the `arm`-arch devices. Thus,
plenty of installation packages provide the binary libraries only for the `arm`
architecture. Our test reveals that, the image of Android 11 (API Level 30)
offers the best support for the `arm`-arch packages on the `amd64` desktops.

Here are several websites offering Android app package downloading:

* [APKCombo](https://apkcombo.com/)
* [APKPure](https://apkpure.com/)
* [CoolApk](https://www.coolapk.com/)

The supported architecture can be checked for the downloaded package on these
platforms, which can be taken as a reference. APKCombo may offer the packages
for various binary architectures. Other app platforms may be explored as well
    to find an available installation package file. We recommend that the
    available installation package or the acquisition approach be released
    together with the constructed task set.

While the installation package file is ready, the app package name and the
activity name of the main activity are to be noted for the task definition
file. In order to know the package name and the main activity name, you can
launch the emulator and install and run the target app, and then execute on the
host machine:

```sh
adb shell am stack list
```

This command will list all the running activities in the format of
`package_name/activity_name` like
`com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity`. Actually, the
package name is the certain name of the Java package, and the activity name is
just the name of the subclass of `android.app.Activity`. Besides, if the app is
in the store of Google Play, the package name can also be obtained from the
`id` field of the webpage's URL. For instance, `com.wikihow.wikihowapp` from
<https://play.google.com/store/apps/details?id=com.wikihow.wikihowapp> is the
package name.

### Preparation of the App Data

Many information apps rely on the Internet to provide dynamic contents.
Therefore, an enough amount of online contents are supposed to be crawled and
stored to guarantee the environment consistency during training and evaluation.
In this way, the agent designer can replay the data to the app through an MitM
proxy during his training and testing. The data should be released along with
the app package and the task definition files.

It is noted that several apps adopt a certificate pinning policy for its SSL
connection. Three [solutions](dynamic-app-zh.md) for this are tested and the
corresponding script tools are provided. When a new task set is released, you
are supposed to make sure that the used app will trust the certificate of the
MitM proxy or at least one of the solutions work if the certificate pinning
policy is adopted and give an explation in the release. If other solutions for
the certificate pinning beyond the recommended three ones is exploited, a guide
and the necessary tools should be provided.

### Definition of the Task Meta-Information

Mobile-Env presents the task meta-information in a `Task` message object of
[ProtoBuf](https://protobuf.dev/) 3. A `Task` message instance in textproto is
required for everay interaction task.

Some references:

* [The definition of `Task` message type](android_env/proto/task.proto)
* [The document of ProtoBuf](https://protobuf.dev/)
* [The syntax definition of
  textproto](https://protobuf.dev/reference/protobuf/textformat-spec/)
