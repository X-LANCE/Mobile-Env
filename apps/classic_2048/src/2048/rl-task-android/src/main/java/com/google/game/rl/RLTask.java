package com.google.game.rl;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Locale;
import java.util.Map;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * Class to handle most RL-task setup <br>
 * <code>
 * adb shell am start -n com.google.example.games.abcd/.MainActivity \
 * --ez "RL_TASK_ENABLED" "true"
 * --es "RL_TASK_GAME_CONFIG" "{\"booleanParam\":true\,\"intParam\":0}"
 * </code> <br>
 * <code>
 *   adb shell am force-stop com.google.example.games.abcd
 * </code>
 */
@SuppressWarnings({"WeakerAccess", "unused"})
public class RLTask implements IRLTask {

  public static final String EXTRA_ENABLED = "RL_TASK_ENABLED";
  public static final boolean EXTRA_ENABLED_DEFAULT = false; // disabled by default
  public static final String EXTRA_GAME_CONFIG = "RL_TASK_GAME_CONFIG";

  private static final boolean LOG_ENABLED = true;
  // adb logcat -s "AndroidRLTask"
  public static final String LOG_TAG = "AndroidRLTask";

  public static final String LOG_MSG_EPISODE_END = "episode end";
  public static final String LOG_MSG_SCORE_AND_SCORE = "score: %s";
  public static final String LOG_MSG_EXTRA_AND_EXTRA = "extra: %s";

  private static RLTask INSTANCE = null;

  private boolean enabled = EXTRA_ENABLED_DEFAULT;

   private RLGameConfiguration gameConfiguration = new RLGameConfiguration();

  public static synchronized RLTask get() {
    if (INSTANCE == null) {
      INSTANCE = new RLTask();
    }
    return INSTANCE;
  }

  private RLTask() {
    super();
  }

  @SuppressWarnings({"BooleanMethodIsAlwaysInverted", "RedundantSuppression"})
  public boolean isEnabled() {
    return enabled;
  }

  public boolean get(String key, boolean defaultValue) {
    return this.gameConfiguration.get(key, defaultValue);
  }

  public int get(String key, int defaultValue) {
    return this.gameConfiguration.get(key, defaultValue);
  }

  public long get(String key, long defaultValue) {
    return this.gameConfiguration.get(key, defaultValue);
  }

  public String get(String key, String defaultValue) {
    return this.gameConfiguration.get(key, defaultValue);
  }

  @Override
  public void logEpisodeEnd() {
    if (!isEnabled()) {
      return;
    }
    log(LOG_MSG_EPISODE_END);
  }

  @Override
  public void logScore(Object score) {
    if (!isEnabled()) {
      return;
    }
    log(String.format(Locale.ENGLISH, LOG_MSG_SCORE_AND_SCORE, score));
  }

  @Override
  public void logExtra(Object extra) {
    if (!isEnabled()) {
      return;
    }
    log(String.format(Locale.ENGLISH, LOG_MSG_EXTRA_AND_EXTRA, extra));
  }

  private void log(String msg) {
    if (!LOG_ENABLED) {
      return;
    }
    Log.i(LOG_TAG, msg);
  }

  public static void logDebug(Object object, String msg) {
    logDebug(object.getClass(), msg);
  }

  public static void logDebug(Class<?> clazz, String msg) {
    Log.d(clazz.getSimpleName(), msg);
  }

  public void nativeLogDebug(String tag, String msg) {
    Log.d(tag, msg);
  }

  public void nativeLogInfo(String tag, String msg) {
    Log.i(tag, msg);
  }

  public void onCreateActivity(Activity activity) {
    processIntent(activity.getIntent());
  }

  public void onCreateActivity(Intent intent) {
    processIntent(intent);
  }

  public void onNewIntentActivity(Intent intent) {
    processIntent(intent);
  }

  private void processIntent(Intent intent) {
    if (intent == null) {
      return;
    }
    Bundle extras = intent.getExtras();
    if (extras == null) {
      return;
    }
    this.enabled = extras.getBoolean(EXTRA_ENABLED, EXTRA_ENABLED_DEFAULT);
    // RLTask.logDebug(this, "processIntent() > this.enabled: " + this.enabled + ".");
    if (this.enabled) {
      String jsonString = extras.getString(EXTRA_GAME_CONFIG);
      // RLTask.logDebug(this, "processIntent() > jsonString: " + jsonString + ".");
      this.gameConfiguration = RLGameConfiguration.from(jsonString);
    }
  }

  /** Game-specific RL-task configuration */
  public static class RLGameConfiguration {

    private final Map<String, Object> config = new HashMap<String, Object>();

    public static RLGameConfiguration from(String jsonString) {
      RLGameConfiguration newGameConfig = new RLGameConfiguration();
      if (jsonString != null && jsonString.length() > 0) {
        try {
          JSONObject jsonObject = new JSONObject(jsonString);
          Iterator<String> keysIt = jsonObject.keys();
          while (keysIt.hasNext()) {
            String key = keysIt.next();
            newGameConfig.put(key, jsonObject.get(key));
          }
        } catch (JSONException e) {
          Log.w(
              RLGameConfiguration.class.getSimpleName(),
              "Error while parsing JSON '" + jsonString + "'!",
              e);
        }
      }
      return newGameConfig;
    }

    public boolean get(String key, boolean defaultValue) {
      Object value = config.get(key);
      if (value instanceof Boolean) {
        return Boolean.parseBoolean(String.valueOf(value));
      }
      return defaultValue;
    }

    public int get(String key, int defaultValue) {
      Object value = config.get(key);
      if (value instanceof Integer) {
        return Integer.parseInt(String.valueOf(value));
      }
      return defaultValue;
    }

    public long get(String key, long defaultValue) {
      Object value = config.get(key);
      if (value instanceof Long || value instanceof Integer) {
        return Long.parseLong(String.valueOf(value));
      }
      return defaultValue;
    }

    public String get(String key, String defaultValue) {
      Object value = config.get(key);
      if (value instanceof String) {
        return String.valueOf(value);
      }
      return defaultValue;
    }

    private void put(String key, Object value) {
      this.config.put(key, value);
    }
  }
}
