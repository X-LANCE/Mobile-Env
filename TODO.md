<!-- vim: set formatoptions+=a: -->

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
* (JPEG compression for transfer): Applied JEPG compression before transferring
  the screen to RemoteSimulator
* (Fuzzy Match): Maybe fuzzy match in text event sources will help. Maybe
  through rapidfuzz library.
* (Beyond `dm_env` interfaces): Will follow new gymnasium to distinguish
  successful finishing and error termination. Will give a DmEnvWrapper instead
  for back-compatibility.
* (Migration to Gymnasium): Migrate GymInterfaceWrapper from deprecated gym to
  gymnasium.
* (Icon Model): The embedded icon model. Maybe I can just use IconNet. But, I
  didn't find a ready-to-use IconNet implementation. Still need to train an own
  one. Found some candidates for icon detection,
  [vision-ui](https://github.com/Meituan-Dianping/vision-ui) and
  [UIED](https://github.com/MulongXie/UIED). However, no icon match model is
  found. I know that this may be a minor demand. So maybe a runnable workaround
  will be implemented first by wrapping these out-of-box tools. And will train
  our own model when I have enough time. Maybe 1 year later, when I'm ready for
  graduation. (> <)
* (Non-ASCII character input through clipboard): I found that clipboard
  synching can copy UTF-8 strings. This may be an idea to enable non-ASCII
  character input.  The emulator gPRC has interfaces to operate clipboard.
* (Non-ASCII character input through emulator gPRC): sendKey interface of the
  emulator may be explored to implement input of UTF-8 strings.
* (FileSystem Events): Events arising from changes in Android file system. Just
  a conceptual idea.
* (Unit Tests): Have a thorough check to the original unit test codes.

---

### Task Sets

* (OpenMoneyBox): I want to define a group of tasks based on OpenMoneyBox.
