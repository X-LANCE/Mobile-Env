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

If you are familiar with the syntax of ProtoBuf 3, we recommend you to compose
the task definition file directly with the help of [the definition of `Task`
message](android_env/proto/task.proto), the following task definition demo, and
[the introduction to the task event management of
Mobile-Env](#definition-of-the-task-events). Otherwise you are recommended to
read the following guides to the message types like `Task`. We will introduce
these types as detailed and clear as possible.

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
   the id comprises only English letters, digits, the underscore and the score.
2. `name` - A string. This field gives a readable task name.
3. `description` - A string briefly explaining the task.
4. `setup_steps` - An array of `SetupStep` messages defining the config
   behaviours to set up a task.
5. `reset_steps` - An array of `SetupStep` messages defining the config
   behaviours during the lauching or restarting of the task.
6. `expected_app_screen` - Optional. This field specifies the running activity
   name and the characteristics of the screen which is used by the platform to
   determine whether the agent has quitted the task app mistakingly during the
   interaction. If it is, the platform will restart the episode in time.

### `SetupStep` Message

### `AppScreen` Message

### Definition of the Task Events
