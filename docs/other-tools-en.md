<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vimc: call SyntaxRange#Include('```ebnf', '```', 'ebnf', 'NonText'): -->

## Other Assistant Tools

### Annotation Tool for Human Demonstration

An annotation tool based on web interface is developed to collect human
demonstrations for behavior cloning approaches. A ready-to-use docker image is
provided for convenience at <https://hub.docker.com/r/zdy023/mobile-env-web>.
The usage of the annotation tool is demonstrated in our [demo
video](https://youtu.be/gKV6KZYwxGY).

Exept for the web interface, a few command line tools are offered for the
preprocessing and visualization of the annotations. The codes are stored at
`../tools/annotation-tool/pkl_tools`.

##### Resaving Tool for the Annotations

The annotations dumped directly by the web interface are saved trajectory by
trajectory in pickle files named as `annotator_name.%d.pkl` where the `%d` is
the index of the trajectory. The resaving tool will assemble the individual
trajectories and resave them according to their tasks. It is invoked as:

```sh
python resave_pickles.py PKL_NAME:S:T DUMPDIR TASKFOLDER
```

+ `PKL_NAME` - The pattern of the path to the trajectory files that should be
  resaved, *e.g.*, `web-dumps/zdy023.%d.pkl`.
+ `S`, `T` - The range of the trajectory indices (inclusive), which are used to
  replace the `%d` in the pattern.
+ `DUMPDIR` - The folder for the re-dumped files.
+ `TASKFOLDER` - The folder of the task definition files.

The format of the re-dumped file is like:

```
{
    "meta": {
        "otask_id": str # The task id declared in the task definition file.
        "otask_name": str # The task name declared in the task definition file.
        "task_definition_id": str # The main file name of the task definition file.
    }
    "trajectories": [
        {
            "task_id": str # This field appears only in the first list element.
            "task": str # This field appears only in the first list element.
            "observation": np.ndarray # The shape is (width, height, 3). The type is float32. The content is the screen image in RGB.
            "view_hierarchy": Optional[str] # The view hierarchy in XML.
            "orientation": np.int64 # Record of the screen orientation.
            "action_type": np.int64 # 0, 1, 2, and 3 as TOUCH, LIFT, REPEAT, and TEXT respectively. This field does not appear in the first list element.
            "touch_position": np.ndarray # The shape is (2,). The type is float32. The values are normalized to [0, 1]. This field does not appear in the first list element and appears only in the steps with action type TOUCH.
            "input_token": str # This field does not appear in the first element and appears only in the steps with action type TEXT.
            “reward": float # This field does not appear in the first element and may not appear in the steps whose reward is 0.
            "instruction": List[str] # This field does not appear in the first element and appears only in the steps triggered the instruction event.
        },
        ...
    ]
}
```

##### Visualization Tool

The re-dumped annotations can be visualized to frames annotating with the
action, reward, instruction, *etc.* for convenient review.

```sh
python visualize_pickle.py PKL_NAME DUMPDIR
```

where

* `PKL_NAME` - The trajectory file to be visualized.
* `DUMPDIR` - The folder where to save the extracted frames.

Every trajectory in the trajectory file will be converted to a group of frames,
which will be saved in a child folder under `DUMPDIR`. This command will print
the path to the frames of each trajectory one by one. Actually, the child foler
for a trajectory is named as
    `task_definition_file_name:trajectory_index%trajectory_counts#trajectory_length`.

The extracted frames can be concatenated to a video by the tools like ffmpeg.
Or the script `make_video_from_pickle.sh` can be adopted to obtain the frames
and the videos in one step:

```sh
./make_video_from_pickle.sh PKL_NAME DUMPDIR
```

##### Annotation Editing Tool

### Task Definition Template Toolkit

TODO
