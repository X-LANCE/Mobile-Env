<!-- vim: set formatoptions+=a: -->
<!-- vimc: syn match Incompleted /\(^\*\)\@<=\ \((\)\@=/: -->
<!-- vimc: syn match Completed /\(^\*\)\@<=\ \(✓\)\@=/: -->
<!-- vimc: syn match Failed /\(^\*\)\@<=\ \(✗\)\@=/: -->
<!-- vimc: syn match Canceled /\(^\*\)\@<=\ \( \)\@=/: -->
<!-- vimc: hi Incompleted ctermbg=yellow: -->
<!-- vimc: hi Completed ctermbg=green: -->
<!-- vimc: hi Failed ctermbg=red: -->
<!-- vimc: hi Canceled ctermbg=white: -->

### Main Branch

* ✓ (Remote environment like OpenAI Universe): Support interaction with
  environment hosted on a remote server. To enable training RL agents on GPU
  servers without KVM enabled.
* ✓ (Partial) (Easier Deployment): Maybe we can construct a docker to simplify
  the deployment of Mobile-Env. Even I feel that it is too complicated to set
  up an Android environment before install Mobile-Env. However, a docker won't
  help KVM configuration, either. Under consideration.
* ✓ (VH Node Specification): Using CSS selector to locate a VH node should be
  easier than the current way
* ✓ (Repeatability control for event slots): I find it useful to control
  repeatability of an event slot. Will implement it when I have the time.
* ✓ (About new event source RHU): Update the annotation tool to support the new
  type of event source.
* ✓ (JPEG compression for transfer): Applied JEPG compression before
  transferring the screen to RemoteSimulator
* ✓ (Fuzzy Match): Maybe fuzzy match in text event sources will help. Maybe
  through rapidfuzz library.
* ✓ (Beyond `dm_env` interfaces): Will follow new gymnasium to distinguish
  successful finishing and error termination. Will give a DmEnvWrapper instead
  for back-compatibility.
* ✓ (Migration to Gymnasium): Migrate GymInterfaceWrapper from deprecated gym
  to gymnasium.
* ✓ (Temporary Storage for Event Values): I think this will be cool if we can
  temporarily store the submitted value of a virtual event and recall it in
  later steps. This will enable interactions between heterochronic events. For
  example, the task manager can note a piece of key information during
  execution and compare it with a later response. This is cool.
* ✓ (Non-ASCII character input through clipboard): I found that clipboard
  synching can copy UTF-8 strings. This may be an idea to enable non-ASCII
  character input.  The emulator gPRC has interfaces to operate clipboard.
* ✗ (Non-ASCII character input through emulator gPRC): sendKey interface of the
  emulator may be explored to implement input of UTF-8 strings.
*  (Non-ASCII character input through a dedicated input method): Follow
   <https://blog.csdn.net/qq_37148270/article/details/109514727> to make a
   solution.
* (FileSystem Events): Events arising from changes in Android file system. Just
  a conceptual idea.
* (Replace pexpect with a self-composing module): As pexpect doesn't work on
  Windows, maybe replace it with a custom module.
* (Other problems on Windows): The main problem seems to lie on uiautomator, or
  the `adb shell`. Maybe change it to `adb exec-out` will solve.
* (Tutorial of how to manage events): I need to supplement a tutorial of how to
  manage events to the current document which simply lists all the fields out.
* ✓ (Replace loggers): Replace loggers of absl with standard loggers.
* (Icon Model): The embedded icon model. Maybe I can just use IconNet. But, I
  didn't find a ready-to-use IconNet implementation. Still need to train an own
  one. Found some candidates for icon detection,
  [vision-ui](https://github.com/Meituan-Dianping/vision-ui) and
  [UIED](https://github.com/MulongXie/UIED). However, no icon match model is
  found. I know that this may be a minor demand. So maybe a runnable workaround
  will be implemented first by wrapping these out-of-box tools. And will train
  our own model when I have enough time. Maybe 1 year later, when I'm ready for
  graduation. (> <)
* (Unit Tests): Have a thorough check to the original unit test codes.
* (Task Debugger): Maybe a debugger for task definition composing? I think a
  visualizer to the event trees is needed.
* ✓ (Long Click): Long click action for VhIoWrapper.
* (Accessibility Forwarding): Maybe have a try on the accessibility forwarder
  to ameliorate the efficiency of VH obtaining following AndroidWorld
* (Investigate the snapshot function of Android Emulator): I want to conduct an
  investigation on the snapshot funciton of Android Emulator. This may help to
  set different initial state for tasks more easily.
* (Simulator based on real mobile devices): Replace the implementation based on
  the gRPC interfaces of Android Emulator in current EmulatorSimulator to pure
  ADB implementations so as to form a simulator that can connect to real mobile
  devices.
* (Task File Format): Maybe desert ProtoBuf and turn to use JSON or YAML.
* (Emulator Metrics): In the future version, Android Emulator may require to
  explicitly specify the whether to collect usage metric data by
  `-metrics-collection` or `-no-metrics` flags.
* (Other Android Emulator Changes): Possible requirement of `-grpc` flag.
  Obsoletion of `-no-skin` flag.

### Annotation Tool

* (Migration to 4.0): Update the annotation-tool to better work with new
  episode end mechanism of 4.0.
* (Keyboard Input for Annotation Tool): Supports free keyboard input for the
  web interface of annoatation tool.

### Template Toolkit

* ✓ (Method to merge into new command): Add a mode to allow to keep only the
  first command in the final result rather than concatenating all the
  intructions.

### Task Sets

* (OpenMoneyBox): I want to define a group of tasks based on OpenMoneyBox.

### Documents

* (Implementation Details): Notes implementation details. Will help future
  maintenance and possible contribution.
  * Structure of `event_listeners` module
  * A figure explaining `cache_until` mechanism
  * Implementation of remote assets
  * Logging system
