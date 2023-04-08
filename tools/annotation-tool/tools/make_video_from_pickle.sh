#!/bin/bash

cmd_path="$(dirname $_)"
pkl_path=$1
video_path=$2

frame_dirs=$(python "$cmd_path"/visualize_pickle.py "$pkl_path" "$video_path")

for f in $frame_dirs; do
	pattern=${f/\%/\%\%}
	ffmpeg -y -framerate 2 -i "$pattern"/%d.jpg "$f".mp4
done
