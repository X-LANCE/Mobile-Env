<!-- vimc: call SyntaxRange#Include('```ebnf', '```', 'ebnf', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```proto', '```', 'proto', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

## Extending a New Environment (App) or a New Task Based on Mobile-Env

To extend a new environment for Mobile-Env platform, you need to prepare:

+ The installation package of the corresponding Android app
+ The necessary external data, *e.g.*, the crawled online data

To extend a new task for Mobile-Env platform, you need to prepare:

+ The task definition file in the text format of [Protocol
  Buffers](https://protobuf.dev/) (ProtoBuf), defining the task id, the task
  description, the setup steps, the episode signals, *etc.*

### Extending New Environment: Preparation of the App Package

You need to prepare the installation package for the app and check if it can be
successfully launched and run on the emulator. Nowadays, most hosts have an
`amd64` CPU, however, most Android mobiles run on the `arm`-arch devices. Thus,
plenty of installation packages provide the binary libraries only for the `arm`
architecture. Our test reveals that, the image of Android 11 (API Level 30)
offers the best support to the `arm`-arch packages on the `amd64`
infrastructure.

Here are several websites offering Android app package downloading:

* [APKCombo](https://apkcombo.com/)
* [APKPure](https://apkpure.com/)
* [CoolApk](https://www.coolapk.com/)

The supported architecture of the package to download is displayed on the web
pages of these platforms and can be taken as a reference. APKCombo may offer
the packages for various binary architectures. Other app platforms may be
explored as well to find a vaild installation package file. We recommend that
the valid installation package or the acquisition approach be distrubuted
together with the new environment or the task set.

### Extending New Environment: Preparation of the App Data

Many information apps rely on the Internet to provide dynamic contents that may
vary according to the spatiotemporal condition of the user.  Therefore, an
enough amount of online contents are supposed to be crawled and stored to
guarantee the environment consistency during evaluation and training.  In this
way, the agent designer can replay the data to the app through an MitM proxy
during the test and training. The data should be released along with the app
package (and the task definition files).

It is noted that many apps adopt a certificate pinning policy for its SSL
connection. Three [certificate unpinning solutions](dynamic-app-en.md) are
tested and the corresponding script tools are provided. When a environment is
released, you are supposed to make sure that the used app will trust the
certificate of the MitM proxy or at least one of the solutions work if the
certificate pinning policy is adopted. Then the solution should be claimed in
the release. If other solutions for the certificate pinning beyond the
recommended three ones is exploited, a guideline and the necessary tools should
be provided.

### Package Name and Main Activity Name

The package name and main activity name are required in task definition files.
In order to know the package name and the main activity name, you can launch
the emulator and install and run the target app, and then execute on the host
machine:

```sh
adb shell am stack list
```

This command will list all the running activities in the format of
`package_name/activity_name`, *e.g.*,
`com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity`. Actually, the
package name is the certain name of the Java package, and the activity name is
just the name of the subclass of `android.app.Activity`. Besides, if the app is
in Google Play store, the package name can also be obtained from the `id` field
of the webpage's URL. For instance, `com.wikihow.wikihowapp` from
<https://play.google.com/store/apps/details?id=com.wikihow.wikihowapp> is the
package name.

### Extending New Task: Task Definition File

A task definition file defines the necessary task configurations includeing the
setup steps, the task goal, step instructions, rewards, the episode end, *etc*.
Mobile-Env accepts a task definition file in the text format of
[ProtoBuf](https://protobuf.dev/) 3 (Protocol Buffers 3). To be specific, each
task definition is a `Task` message object.

Some references:

* [The definition of `Task` message type](../android_env/proto/task.proto)
* [The documents of Protocol Buffers](https://protobuf.dev/)
* [The syntax definition of the text format of Protocol
  Buffers](https://protobuf.dev/reference/protobuf/textformat-spec/)

If you are familiar with the syntax of ProtoBuf 3, we recommend you to compose
the task definition file directly with the help of [the definition of `Task`
message](../android_env/proto/task.proto), the following task definition demo,
and [the introduction to the timing of episode signals in
Mobile-Env](#extending-new-task-timing-of-episode-signals). Otherwise you are
recommended to read the following guides to the message types like `Task`. We
will introduce these types as detailedly and clearly as possible.

<!-- Task Definition Demo {{{ -->
<details>
    <summary>Here is a demo task definition. You can expand to view it.</summary>

```
id: "bake_lobster_tails-7"
name: "WikiHow Search Task - How to bake lobster tails"
description: "A demo task primitive requiring to search WikiHow for a specific article.\nA demo task primitive requiring to access a specific article.\nA demo task asking to check the reference list."

setup_steps: {
  adb_call: {
    install_apk: {
      filesystem: {
        path: "../wikiHow：万事指南_2.9.6_apkcombo.com.apk"
      }
    }
  }
}
setup_steps: {
  adb_call: {
    rotate: {
        orientation: PORTRAIT_0
    }
  }
}

reset_steps: {
  adb_call: {
    force_stop: {
      package_name: "com.wikihow.wikihowapp"
    }
  }
}
reset_steps: {
  adb_call: {
    clear_cache: {
      package_name: "com.wikihow.wikihowapp"
    }
  }
}
reset_steps: {
  success_condition: {
    num_retries: 10
    wait_for_app_screen: {
      app_screen: {
        activity: "com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity"
      }
      timeout_sec: 10.0
    }
  }
  adb_call: {
    start_activity: {
      full_activity: "com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity"
    }
  }
}
reset_steps: {
  adb_call: {
    start_screen_pinning: {
      full_activity: "com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity"
    }
  }
}

expected_app_screen: {
  activity: "com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity"
}

max_num_steps: 500

event_sources: {
  text_recognize: {
    expect: "\\b\\(bake\\|lobster\\|tails\\)\\b"
    rect: {
      x0: 0.2439
      y0: 0.0354
      x1: 0.9085
      y1: 0.1171
    }
  }
  id: 1
}
event_sources: {
  view_hierarchy_event: {
    view_hierarchy_path: "android.widget.FrameLayout"
    view_hierarchy_path: "android.widget.LinearLayout@com.wikihow.wikihowapp:id/action_bar_root"
    view_hierarchy_path: "android.widget.FrameLayout@android:id/content"
    view_hierarchy_path: "androidx.appcompat.widget.LinearLayoutCompat@com.wikihow.wikihowapp:id/action_search"
    view_hierarchy_path: "android.widget.LinearLayout@com.wikihow.wikihowapp:id/search_bar"
    view_hierarchy_path: "android.widget.LinearLayout@com.wikihow.wikihowapp:id/search_edit_frame"
    view_hierarchy_path: "android.widget.LinearLayout@com.wikihow.wikihowapp:id/search_plate"
    view_hierarchy_path: "android.widget.EditText@com.wikihow.wikihowapp:id/search_src_text"
    properties: {
      property_name: "text"
      pattern: "\\b\\(bake\\|lobster\\|tails\\)\\b"
    }
    properties: {
      property_name: "clickable"
      pattern: "true"
    }
  }
  id: 2
}
event_sources: {
  log_event: {
    filters: "jd:D"
    pattern: "\\bmUrl is: https://www\\.wikihow\\.com/wikiHowTo\\?search=.*(bake|lobster|tails).*"
  }
  id: 3
}

event_sources: {
  text_detect: {
    expect: "How to Bake Lobster Tails"
    rect: {
      y0: 0.19
      x1: 1.0
      y1: 0.3
    }
  }
  id: 5
}
event_sources: {
  log_event: {
    filters: "jd:D"
    pattern: "\\bmUrl is: https://www\\.wikihow\\.com/Bake-Lobster-Tails"
  }
  id: 6
}
event_sources: {
  view_hierarchy_event: {
    view_hierarchy_path: "android.widget.FrameLayout"
    view_hierarchy_path: "android.widget.LinearLayout@com.wikihow.wikihowapp:id/action_bar_root"
    view_hierarchy_path: "android.widget.FrameLayout@android:id/content"
    view_hierarchy_path: "android.drawerlayout.widget.DrawerLayout@com.wikihow.wikihowapp:id/drawer_layout"
    view_hierarchy_path: "android.webkit.WebView"
    view_hierarchy_path: "android.view.View@mw-mf-viewport"
    view_hierarchy_path: "android.view.View@mw-mf-page-center"
    view_hierarchy_path: "android.view.View@content_wrapper"
    view_hierarchy_path: "android.view.View@content_inner"
    view_hierarchy_path: "android.view.View@section_0"
    view_hierarchy_path: "android.widget.TextView"
    properties: {
      property_name: "text"
      pattern: "How to Bake Lobster Tails"
    }
  }
  id: 7
}

event_sources: {
  text_detect: {
    expect: "References"
    rect: {
      x1: 0.33
      y1: 1.0
    }
  }
  id: 9
}
event_sources: {
  log_event: {
    filters: "jd:D"
    pattern: "\\burl is: https://www\\.wikihow\\.com/Bake-Lobster-Tails\\?wh_an=1&amp=1#References\\b"
  }
  id: 10
}

event_slots: {
  reward_listener: {
    type: OR
    events: {
      event: {
        type: OR
        id: 4
        events: [
            { id: 1 },
            { id: 2 },
            { id: 3 }
        ]
        transformation: "y = 1"
      }
    }
    events: {
      event: {
        type: OR
        id: 8
        events: [
            { id: 5 },
            { id: 6 },
            { id: 7 }
        ]
        transformation: "y = 1"
      }
    }
    events: {
      event: {
        type: OR
        id: 11
        events: [
            { id: 9 },
            { id: 10 }
        ]
        transformation: "y = 1"
      }
    }
  }

  episode_end_listener: {
    events: {
      id: 11
    }
    transformation: "y = True"
  }

  instruction_listener: {
    type: OR
    events: {
      event: {
        events: {
          id: 4
        }
        transformation: "y = [\'Access the article \"How to Bake Lobster Tails\"\']"
      }
    }
    events: {
      event: {
        events: {
          id: 8
        }
        transformation: "y = [\'Check the reference list\']"
      }
    }
  }
}
command: "Search an article to learn how to bake lobster tails."
command: "Then, access the article \"How to Bake Lobster Tails\""
command: "Then, check the reference list"
vocabulary: ["how to", "tails", "lobster", "bake"]
```
</details>
<!-- }}} Task Definition Demo -->

To instantiate a `Task` message, the following parameters need to be specified:

1. `id` - A string as the task id to identify the tasks. It is recommended that
   the id comprises only English letters, digits, the underscore and the short
   dash.
2. `name` - A string. This field gives a readable task name.
3. `description` - A string briefly explaining the task.
4. `setup_steps` - An array of `SetupStep` messages defining the steps to set
   up a task.
5. `reset_steps` - An array of `SetupStep` messages defining the steps to
   launch or restart a task.
6. `expected_app_screen` - Optional. This field specifies the running activity
   name and the characteristics of the screen. This information is used by the
   platform to determine whether the agent has quitted the task app mistakenly
   during the interaction. If it is, the platform will reset the episode in
   time.
7. `max_duration_sec` - A floating number. If the episode fails to end in the
   given seconds, the platform will force it to restart. You can ignore this
   field or set a non-positive number to disable this feature.
8. `max_num_steps` - An integer. Similar to `max_duration_sec`, the platform
   will restart the episode if it does not end after the specified steps.
   Ignoring this field or setting a non-positive number will disable this
   feature.
9. `event_sources` - Defines the event sources. Event sources are referred to
   in [the following section](#extending-new-task-timing-of-episode-signals)
   and the [paper](https://arxiv.org/abs/2305.08144).
10. `event_slots` - Defines the timing of the episode signals. See the
    [paper](https://arxiv.org/abs/2305.08144) for a brief introduction.
    Details are presented in [the following
    section](#extending-new-task-timing-of-episode-signals).
11. `extra_spec` - Defines the specification of the task extras. This is kept
    for the compatility of AndroidEnv.
12. `command` - An array of string providing a description or a global command
    for the task target which will be sent to the agent.
13. `vocabulary` - An array of string providing a tiny vocabulary corresponding
    to the task. This vocabulary can be used to remit the difficulty of the
    task and the annotation of human demonstration.

More message types are requird to define `setup_steps`, `reset_steps`,
`expected_app_screen`, `event_sources`, and `event_slots` and will be
introduced below.

### Extending New Task: `SetupStep` Message

<!-- `SetupStep` Message {{{ -->
A `SetupStep` array is required by the `setup_steps` and `reset_steps` fields.
Each `SetupStep` message defines a configuration step.

The `SetupStep` message defines two fields:

* `success_condition` - Defines an operation to check if the step succeeds.
* `step` - Defines the certain configuration operation.

At least one field should be defined. The `step` will be executed first to
complete the config, then the `success_condition` will be executed to check the
success if both fields are specified.

A message object is required for `success_condition`, which contains two
fields:

<!-- `success_condition` Field {{{ -->
<details>
    <summary>The details about the `success_condition` field.</summary>

* `num_retries` - The maximum attempt times if the step fails. The platform
  will try at least 3 times even though it is ignored or a value smaller than 3
  is specified.
* `check` - The certain check operation.

`check` is an exclusive field decorated with [`oneof`
keyword](https://protobuf.dev/programming-guides/proto3/#oneof). Only one
sub-field should be chosen from three options. The options (operations) are:

* `wait_for_app_screen` - Requires to wait for a specific screen. An
  `AppScreen` message should be provided through the `app_screen` field. The
  `AppScreen` message determines a screen through the activity name and the
  view hierarchy (VH) characteristics of the screen. The details are presented
  in the following section.
* `check_install` - Checks if a specific app package is installed. The package
  name is specified through the `package_name` field.
* `wait_for_message` - Waits for a specific message from the system logs. A
  regex for the waited message is expected to be provided through the `message`
  field. The regex's syntax follows the [`re` module of
  Python](https://docs.python.org/3/library/re.html).

Besides, all the aforementioned three operations require a float field
`timeout_sec` to specify the timeout, *e.g.*, 10 seconds. If the `timeout_sec`
field is ignored, then the whole check operation will not be executed.
</details>
<!-- }}} `success_condition` Field -->

`step` is also a `oneof` field with two options:

* `sleep` - Sleeps for several seconds. This field requires a message in which
  the sleeping seconds should be specified through the float field `time_sec`.
* `adb_call` - Revokes an ADB command. An `AdbCall` message object is required.

<!-- `AdbCall` Message {{{ -->
<details>
    <summary>The details about the `AdbCall` message.</summary>

`AdbCall` message is defined in
[`android_env/proto/adb.proto`](../android_env/proto/adb.proto) and supports
many kinds of operations. Some frequently-used operations comprise:

* `install_apk` - Installs a package. The path to the apk package is expected
  in the string field `path` of the message field `filesystem`. The path can be
  specified either as a relative path from the current `textproto` file or as
  an absolute path (not recommended).
* `force_stop` - Forces a process to terminate according to the package name
  provided by `package_name`.
* `clear_cache` - Clears the app's cache according to the package name provided
  by `package_name`.
* `start_activity` - Launches an Android activity whose name is specified by
  `full_activity`. The format of the Android activity identification is
  `package_name/activity_name`, *e.g.*,
  `com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity`.
* `start_screen_pinning` - Enables screen pinning. After enabling, the Android
  system will switch back to the certain activity if an exit is detected. The
  activity should be specified through `full_activity`.
</details>
<!-- }}} `AdbCall` Message -->
<!-- }}} `SetupStep` Message -->

### Extending New Task: `AppScreen` Message

<!-- `AppScreen` Message {{{ -->
An `AppScreen` message object is required for the argument of both
`expected_app_screen` and `wait_for_app_screen`. This type of message needs two
parameters:

+ `activity` - A string indicating an Android activity. The format is
  `package_name/activity_name`, *e.g.*,
  `com.wikihow.wikihowapp/com.wikihow.wikihowapp.MainTabActivity`.
+ `view_hierarchy_path` - An array of string requiring a VH path.  Each array
  element is be a regex which matches an item on the path. The VH path
  comprises a VH node sequence from the root to the leaf. It is not necessary
  to provide the nodes consecutively.

It is worth noting that, the representation of the nodes in
`AppScreen.view_hierarchy_path` is the same with the output of the command `adb
shell dumpsys`, *i.e.* the output of `android.view.View::toString`. This is a
quite compat format and hard to read. However, in most cases, this property can
be ignored. This is due to that this property will locates to a specific page,
while most InfoUI interaction tasks require transferring between different
pages of the app. Consequently, this property shouldn't be used to fix the
interaction to a specific page. If you really need to give a value to this
property, you can refer to the following example:

<details>
    <summary>The example of the `view_hierarchy_path` property</summary>

```
view_hierarchy_path: [
    "^DecorView@.*\[MainActivity\]$",
    "^android.widget.LinearLayout\{.*\}$",
    "^android.widget.FrameLayout\{.*android\:id\/content\}",
    "^android.widget.RelativeLayout\{.*\}",
    "^android.widget.FrameLayout\{.*app\:id\/fragment_holder\}",
    "^android.widget.RelativeLayout\{.*\}",
    "^com.google.example.games.nostalgicracer.views.RaceView3D\{.*app\:id\/gameplay_screen_3d\}",
]
```
</details>

If you really need to specify a node's property detailedly, you can refer to
the following EBNF and the source code of `android.view.View::toString`.

<!-- The Output Format and Source Code of View::toString {{{ -->
<details>
    <summary>Expand to check the output format and the source code of
    `android.view.View::toString`.</summary>

The EBNF definition of the output format of `android.view.View::toString`:

```ebnf
view-hierarchy-line = class-name
    , "{" object-hash-code
    , " " view-flags
    , " " private-flags
    , " " bbox
    , [ " #" element-id-code
      , [ " " resource-package-name
        , ":" resource-type-name
        , "/" resource-entry-name
        ]
      ]
	, "}" ;

view-flags = visibility-flag
    , focusable-flag
    , enabled-flag
    , draw-flag
    , scrollbars-horizontal
    , scrollbars-vertical
    , clickable
    , long-clickable
    , context-clickable ;

private-flags = is-root-namespace
    , focused
    , selected
    , pressed-flag
    , hovered
    , activated
    , invalidated
    , dirty-flag ;

bbox = left "," top "-" right "," bottom ;
left = integer-symbol ;
top = integer-symbol ;
right = integer-symbol ;
bottom = integer-symbol ;

visibility-flag = "V" (* Visible *)
    | "I" (* Invisible *)
    | "G" (* Gone *)
    | "." ;
focusable-flag = "F" | "." ;
enabled-flag = "E" | "." ;
draw-flag = "D" (* Will Draw *)
    | "." ;
scrollbars-horizontal = "H" | "." ;
scrollbars-vertical = "V" | "." ;
clickable = "C" | "." ;
long-clickable = "L" | "." ;
context-clickable = "X" | "." ;

is-root-namespace = "R" | "." ;
focused = "F" | "." ;
selected = "S" | "." ;
pressed-flag = "p" (* Prepressed *)
    | "P" (* Pressed *)
    | "." ;
hovered = "H" | "." ;
activated = "A" | "." ;
invalidated = "I" | "." ;
dirty-flag = "D" | "." ;
```

The source code of `android.view.View::toString` from Android API 27:

```java
public String toString() {
	StringBuilder out = new StringBuilder(128);
	out.append(getClass().getName());
	out.append('{');
	out.append(Integer.toHexString(System.identityHashCode(this)));
	out.append(' ');
	switch (mViewFlags&VISIBILITY_MASK) {
		case VISIBLE: out.append('V'); break;
		case INVISIBLE: out.append('I'); break;
		case GONE: out.append('G'); break;
		default: out.append('.'); break;
	}
	out.append((mViewFlags & FOCUSABLE) == FOCUSABLE ? 'F' : '.');
	out.append((mViewFlags&ENABLED_MASK) == ENABLED ? 'E' : '.');
	out.append((mViewFlags&DRAW_MASK) == WILL_NOT_DRAW ? '.' : 'D');
	out.append((mViewFlags&SCROLLBARS_HORIZONTAL) != 0 ? 'H' : '.');
	out.append((mViewFlags&SCROLLBARS_VERTICAL) != 0 ? 'V' : '.');
	out.append((mViewFlags&CLICKABLE) != 0 ? 'C' : '.');
	out.append((mViewFlags&LONG_CLICKABLE) != 0 ? 'L' : '.');
	out.append((mViewFlags&CONTEXT_CLICKABLE) != 0 ? 'X' : '.');
	out.append(' ');
	out.append((mPrivateFlags&PFLAG_IS_ROOT_NAMESPACE) != 0 ? 'R' : '.');
	out.append((mPrivateFlags&PFLAG_FOCUSED) != 0 ? 'F' : '.');
	out.append((mPrivateFlags&PFLAG_SELECTED) != 0 ? 'S' : '.');
	if ((mPrivateFlags&PFLAG_PREPRESSED) != 0) {
		out.append('p');
	} else {
		out.append((mPrivateFlags&PFLAG_PRESSED) != 0 ? 'P' : '.');
	}
	out.append((mPrivateFlags&PFLAG_HOVERED) != 0 ? 'H' : '.');
	out.append((mPrivateFlags&PFLAG_ACTIVATED) != 0 ? 'A' : '.');
	out.append((mPrivateFlags&PFLAG_INVALIDATED) != 0 ? 'I' : '.');
	out.append((mPrivateFlags&PFLAG_DIRTY_MASK) != 0 ? 'D' : '.');
	out.append(' ');
	out.append(mLeft);
	out.append(',');
	out.append(mTop);
	out.append('-');
	out.append(mRight);
	out.append(',');
	out.append(mBottom);
	final int id = getId();
	if (id != NO_ID) {
		out.append(" #");
		out.append(Integer.toHexString(id));
		final Resources r = mResources;
		if (id > 0 && Resources.resourceHasPackage(id) && r != null) {
			try {
				String pkgname;
				switch (id&0xff000000) {
					case 0x7f000000:
						pkgname="app";
						break;
					case 0x01000000:
						pkgname="android";
						break;
					default:
						pkgname = r.getResourcePackageName(id);
						break;
				}
				String typename = r.getResourceTypeName(id);
				String entryname = r.getResourceEntryName(id);
				out.append(" ");
				out.append(pkgname);
				out.append(":");
				out.append(typename);
				out.append("/");
				out.append(entryname);
			} catch (Resources.NotFoundException e) {
			}
		}
	}
	out.append("}");
	return out.toString();
}
```
</details>
<!-- }}} The Output Format and Source Code of View::toString -->
<!-- }}} `AppScreen` Message -->

### Extending New Task: Timing of Episode Signals

Step instructions, rewards, the episode end, *etc.* are called *episode
signals*, or *event slots* in the task definition file. To be specific, there
are 6 different event slots:

+ Score event (`score_listener`)
+ Reward event (`reward_listener`)
+ Episode end event (`episode_end_listener`)
+ Instruction event (`instruction_listener`)
+ Extra info event (`extra_listener`)
+ JSON extra info event (`json_extra_listener`)

The event slots are corresponding to the signals the agent will receive from
the environment. The triggering state of an event slot depends on the *event
sources*. An event source indicates a specific pattern for the OS feedback.
Given a triggering state of an event slot $t$, matching states of a group of
event sources $S = \{s_1, s_2, \dots, s_n\}$, the simplified triggering logic
can be formalized as
$$
t = f(s_1, s_2, \dots, s_n),
$$
where ther triggering function $f$ is a boolean function. There are 4 types of
OS feedback that can be used for event sources:

+ Screen texts (`text_recognize`, `text_detect`)
+ Scrren icons (`icon_recognize`, `icon_detect`, `icon_match`,
  `icon_detect_match`)
+ View hierarchy (`view_hierarchy_event`)
+ System log (`log_event`)

Here is a demonstration of event triggering logic $f$ with diverse operating
system feedback. The triggering state $t$ of the event slot depends on a
combinatorial boolean logic of the matching states $s_i$ of multiple event
sources. `Text`, `VH`, and `Log` indicate different types of OS feedback.

![Demonstration of Event Triggering Logic with Diverse Operating System
Feedback](images/demo-event-tree.png)

In addition to the combinatorial logic form of boolean function $f$, we
introduce "prerequisite" mechanism to correctly handle the step order for
multistep tasks. To be specific, we call each node (including the event sources
at leaves and the `And` and `Or` operators inside) on the tree representation
of $f$ a *virtual event*. If virtual event $a$ is declared as the prerequisite
of virtual event $b$ in the task definition file, then event $b$ will not be
triggered until event $a$ has already been triggered ever in one episode. For
example, an order is supposed to be placed ($b$) only after all the information
fields have been filled in ($a$), thus, information filling can be declared as
the prerequisite of order placing to guarantee such a constraint.  After each
interaction step during episode, a virtual event will first check if its
prerequisites are satisfied and then decide its triggering flag according to
the matching state (for event sources) or the triggering flags of its children
(for `And` and `Or`).

#### Event Sources and Event Slots

This section will elaborate on the event sources and event slots.

##### The Input and Output of the Event Sources

This section will introduce the different types of system feedback listend by
the event sources and their outputs applied to the parent nodes.

The two kinds of screen text event sources listen the the text contents on the
screen, which should be enabled by an external OCR module. The source with
detection will run a detection model to detect the text instances in the
specified region before recognizing the certain contents, while the source with
only recognition directly run the recognition model based on the assumption
that the specified region is well aligned to the text instance's boundary.
After the contents are recognized, the platform will try to match the results
by the regex in the event source definition. If the results match the regex and
the triggering condition is satisfied, this event will be triggered. Then the
text event source will return a tuple comprising all the captured groups, which
is just the returning value of
[`re.Match.groups`](https://docs.python.org/3/library/re.html#re.Match.groups).

The four kinds of screen icon event sources listen to the icons on the screen,
which should be enabled by an external icon recognition and matching module.
The source with detection will fisrt invoke detection model and then
recognition or mathing model, which is the same with the text sources. The
sources for recognition will classify the icon instance using a recognition
model and check if the predition matches the class in the evenet source
definition. In contrast, a source for matching will take a mathing model to
decide if the input icon instance matches with a reference image. If the
recognized class is right or the reference is matched, the event source will be
triggered according to the aforementioned triggering conditions. If the event
source is triggered, a boolean true `True` will be returned to the parent.

A VH event source will take the VH of the current screen and check if there is
a specific node and if the node's properties satisfy some constraints. If the
node exists and the property constraints are satisfied, the event source will
be triggered according to the aforementioned triggering conditions.  A
triggered event source will return a list storing the values of the checked
properties. However, it is worth noting that the VH events will not be checked
after every step. Owing to the high latency of the acquisition through ADB and
the high length of the VH XML, conflicts of the output can occur if request is
too fast. Hence, the platform slows down the check frequency of the VH.
Consequently, there is no guarantee that the VH event source can be triggered
in time.  Therefore, the crucial task events shouldn't rely solely on the VH
event sources.

A system log event source will listen to the runtime log of the system and
matches each line with the regex in the definition. If any line is matched and
the aforementioned triggering conditions are satisfied, the event source will
be triggered and return a tuple comprising all the regex-captured groups, which
is the same with the screen text event sources.

##### The Event Slots

This section will introduce the six event slots designed for the platform. The
event slots are corresponding to the episode signalsthat the agents can have a
perception to.

The slots of the score event (`score_listener`) and the reward event
(`reward_listener`) are designed for the parsing of the reward which are to be
returned to the agent. Their difference is the explanation to the received
signal. The score event slot regards the received signal as an accumulated
score, *i.e.*, the platform will subtract the last recorded score from the
novel one to get the single-step reward, if a score event is triggered. In
contrast, the reward event slot considers the received signal to be the
single-step reward, thus the value will be returned directly. The resulted
single-step reward from these two slots will be added and then returned to the
agent.

The episode end event slot (`episode_end_listener`) indicated if the episode
comes to the end and the platform will restart the task at the next step. This
usually means that the agent has just achieved the task target. But it is also
possible that several severe errors have occured and the system cannot resume
and has to restart. Only the triggering flag of this event slot makes sense and
it returns no further values to the agent.

The instruction event slot (`instruction_listener`) gives the agent the novel
step supplementary instructions during the interaction. This slot accepts and
returns a string list, in which each element is a line or a sentence of
instruction.

The extra info and the JSON extra info is the task-specific extra info which is
not included in the observation and may assist the agent in making a decision.
These items are proposed in AndroidEnv. The extra info event slot
(`extra_listener`) expects a dict like `Dict[str, List[Any]]` with the strings
as the keys and the lists storing some data as the values. The JSON extra info
event slot (`json_extra_listener`) expects a JSON string which should be parsed
into the same format with that of the extra slot. The signals from the two
slots will be mixed before returning to the agent.

#### Define the Event Sources through `event_sources`

Patterns for OS feedback are defined through `event_sources` field in the task
definition file. Then at runtime, the instances of the event sources will check
if received OS feedback matches the defined pattern and decide if the event
should be triggered. To define an event source, you need to specify three
properties:

+ `event` - A `oneof` field defining the particular pattern to be recognized.
+ `id` - A 32-bit interger providing the unique id of the event source for
  later referencing. *The id is required to be a **positive** number*.
+ `repeatability` - An enum from `NONE`, `LAST`, and `UNLIMITED`. This field
  indicates if the event should be triggered repeatedly when the pattern
  defined by `event` is satisfied continuously. The value defaults to `NONE`.
  - `NONE` indicates to never trigger again in an episode, *i.e.*, the event
    can be triggered by one input only once in an episode.
  - `LAST` indicates not to trigger continuously. If the identical input
    matched with the pattern is met continuously, then only the first match
    will trigger the event. However, if the identical input is met again after
    some different inputs, the event can be triggered as before.
  - `UNLIMITED` makes no constraints for the repeatability, Once the feedback
    meets the defined pattern, the event will be triggered.

The options of `event` is the aforementioned event sources:

+ `text_recognize`, `text_detect` - These two sources recognizes/detects the
  text contents in the particular region on the screen. The required fields are
  + `expect` - A regex for the expected texts.
  + `rect` - Expects a message with four float properties: `x0`, `y0`, `x1`,
    and `y1` to indicate the screen region where the recognition/detection is
    conducted. The coordinates are expected to be normalized to `[0, 1]`.
+ `icon_recognize`, `icon_detect` - These two sources recognizes/detects the
  icon contents in the particular region on the screen. They needs:
  + `class` - A string as the certain name of the icon class. The name set
    depends on the mounted icon model.
  + `rect` - Gives the region for the recognition/detection, which is the same
    with the text event sources.
+ `icon_match`, `icon_detect_match` - These two sources recognizes/detects the
  icon contents in the particular region on the screen. In contrast to
  `icon_recognize` and `icon_detect`, these two event sources check if the icon
  matches with a reference. The required fields are
  + `path` - The path to the reference image. Either a relative path from the
    definition file or an absolute path is acceptable. (The latter one is not
    recommended.)
  + `rect` - The same with the events above.
+ `view_hierarchy_event` - Matches the contents in the VH and expects:
  + `view_hierarchy_path` - The VH path to a specific VH node. The format is
    fairly more readable compared to that in `AppScreen`, which will be
    detailed below.
  + `properties` - The list of the properties to check of the VH node indicated
    by `view_hierarchy_path`. To check a property, you need to provide:
    - `property_name` - The property name. The property name is the name of the
      node attribute in the VH XML acquired through the command `adb shell
      uiautomator dump`. Besides, four virtual properties, `left`, `top`,
      `right`, and `bottom`, are enabled for convenience, which are
      corresponding to the four coordinates in the `bounds` attribute in the
      XML respectively.
    - `sign` - Works only for the numeric properties and specifies the
      comparison approach of the reference value with the runtime read value.
      The reference value in the definition is the first operand of the
      comparators. The supported comparators are `EQ` (equal to), `LE` (less
      than or equal to), `LT` (less than), `GE` (greater than or equal to),
      `GT` (greater than), and `NE` (inequal to).
    - `property_value` - A `oneof` field for the reference value:
      * `pattern` - A regex for a string property
      * `interger` - An integer reference
      * `floating` - A floating reference
+ `log_event` - Matches the system log lines and requires two fields:
  - `filters` - An array of string for the log filters like `jd:D`. The system
    logs are obtained by the command `adb logcat -v epoch FILTERS *:S`, where
    `FILTERS` is all the filter names declared in the definition. All the
    filters declared across the log event sources in the definition file will
    be merged (with duplicates removed) before invoking the ADB command.
  - `pattern` - The regex for the expected log line.

The VH node in the definition of the VH event sources is specified as
`class_pattern@id_pattern`. Here two regexes are expected before and after the
`@`. `class_pattern` matches `class` property of the node, which is commonly
the Java class name of the node. `id_pattern` matches `resource-id` property of
the node. `id_pattern` together with the preceding `@` can be ignored. If an
`@` appears in the regexes, it should be escaped by `\`.

#### Define the Virtual Event Trees for the Event Slots through `event_slots`

The `event_slots` field expects a message object in which the properties are
defined for the aforementioned 6 event slots. Each property expects an event
tree. The properties can be ignored for that this event slot will never be
triggered.

An event tree is represented by an `EventSlot` message. Each `EventSlot`
message constitutes a virtual event node on the event tree. It has the
following properties:

+ `type` - An enum from `SINGLE`, `AND`, `OR`. The default value is `SINGLE`
+ `id` - A 32-bit integer as the id of the virtual event. Note that all the
  nodes on the event tree and the event sources share the same id space. Thus,
  this id shouldn't be the same with an existing id to prevent conflicts. *An
  id should be a **positive** number.* The id is optional and can be ignored if
  the virtual event will not be referenced.
+ `events` - An array defining the child nodes sequentially. Only the first
  element is used for a `SINGLE` node.
+ `prerequisite` - An array of 32-bit interger. The other virtual events are
  referenced by their id through this field as the prerequisites of the current
  node. In an episode, the current node can be triggered only if all the
  prerequisites have been triggered ever. This field can be ignored.
+ `transformation` - An array of string expecting a series of Python statements
  defining a transformation to handle the signals applied by the child nodes.
  If this field is ignored, then the transformation will be regared as an
  identity transformation.

##### Definition of the Child Event Nodes

The child event nodes are defined by a message containing only a `oneof` field.
The available fields are:

+ `id` - Expects a 32-bit interger as the reference to a virtual event's id.
+ `event` - Expects a new `EventSlot` message as the definition of the child
  event.

##### Definition of the Transformation

A group of Python statements can be offered through the `transformation`
property to process the signals applied by the child nodes. The statements will
be executed by `exec` sequentially. In the statements, the input from the child
nodes can be referenced as the variable `x` and the processing result is
expected to be stored in the variable `y`. The transformation defined in
`transformation` in an `OR` nodes will be applied to the inputs from the
different children respectively, thus, there is only the value from a single
child stored in `x`. In contrast, the defined transformation in an `AND` node
will be applied to the ensemble of the outputs from all its children, in which
case the type of `x` will be `List[List[T]]`. The length of the outer list is
just the number of the child events and the elements are corresponding to the
children respectively. The length of the inner list is 1 in most situations.
While multiple results may be returned by the system log event sources if
multiple lines are matched or the event sources with detection if multiple
instances are detected.
