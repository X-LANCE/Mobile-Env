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
* (Icon Model): The embedded icon model. Maybe I can just use IconNet. But, I
  didn't find a ready-to-use IconNet implementation. Still need to train an own
  one.
* (FileSystem Events): Events arising from changes in Android file system. Just
  a conceptual idea.
* (Fuzzy Match): Maybe fuzzy match in text event sources will help. Maybe
  through rapidfuzz library.
* (Non-ASCII character input): I found that clipboard synching can copy UTF-8
  strings. This may be an idea to enable non-ASCII character input.
* (About new event source RHU): Update the annotation tool to support the new
  type of event source.
* (Migration to Gymnasium): Migrate GymInterfaceWrapper from deprecated gym to
  gymnasium.

---

### Task Sets

* (OpenMoneyBox): I want to define a group of tasks based on OpenMoneyBox.
