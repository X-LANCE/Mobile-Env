from android_env.proto import task_pb2
import os.path

def fix_path(task: task_pb2.Task, task_directory: str) -> task_pb2.Task:
    """
    Fixes the path setting in `task` and return it back.

    Args:
        task (task_pb2.Task): task config object
        task_directory (str): the path which is expected to be the base path,
          usually is the directory of the task config file

    Return:
        task_pb2.Task: task config object with the fixed path
    """

    for st in task.setup_steps:
        _fix(st, task_directory)
    for st in task.reset_steps:
        _fix(st, task_directory)
    return task

def _fix(setup: task_pb2.SetupStep, task_directory: str):
    if st.HasField("adb_call")\
            and st.adb_call.HasField("install_apk"):
        apk_path = st.adb_call.install_apk.filesystem.path
        if not os.path.isabs(apk_path):
            st.adb_call.install_apk.filesystem.path =\
                    os.path.normpath(os.path.join(task_directory, apk_path))
