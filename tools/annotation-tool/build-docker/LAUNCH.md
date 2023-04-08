1. Mount I/O volume:
   + `/data/dump` - to store the dumped action records
   + `/data/task_path` - to store the task apk and definitions which are store under `tasks` subfolder
2. Map web port: 5000
3. Give launching arguments:
   1. wikihow server address
   2. wikihow server port
   3. the name of the annotator which will be used in the name of the dumped file
   4. the domain names to be replayed seperated by space
4. Mount kvm volume `/dev/kvm`
