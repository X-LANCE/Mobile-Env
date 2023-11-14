<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

# Annotation Tool for Human Demonstration

### Initiate NPM

```sh
cd frontend
npm install
```

### Build the Frontend

```sh
cd frontend
npm run build
```

### Build the Backend

```sh
make backend
```

### Launch the Backend

```sh
python backend/server.py DUMPPATH TASK_DIFINITION_PATH
```

* `DUMPPATH` - the path of the pkl file to dump the collected annotation
* `TASK_DIFINITION_PATH` - the folder where the task definition files are stored

### Build the Docker

Please refer to [BUILD.md](build-docker/BUILD-en.md).
