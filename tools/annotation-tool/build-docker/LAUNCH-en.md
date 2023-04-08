<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->

### Quick Usage

```sh
docker run -it\
    -v OUTPUT_DIR:/data/dump\
    -v INPUT_DIR:/data/task_path\
    -p 127.0.0.1:5000:5000\ # map the port of the webpage interface
    --device /dev/kvm\ # mount the kvm device
    zdy023/mobile-env-web:latest\
    10.0.0.1 8081 "zdy023" www.wikihow.com www.example.com
```

Arguments:
1. Address to the replay server
2. Port to the replay server
3. Annotator's name used in the dumped pickle file
4. domains to replay

Then access <http://127.0.0.1:5000> in the browser to open the annotation UI. Press `Ctrl+C` once in the terminal to close the docker after closing the webpage interface.

The structure of the `INPUT_DIR`:

```
INPUT_DIR
├── tasks
│   ├── 180_on_a_scooter-8.textproto
│   ├── add_a_contact_on_whatsapp-8.textproto
│   ├── address_a_letter_to_england-7.textproto
│   └── ...
└── wikiHow_apkcombo.com.apk
```
