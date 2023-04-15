<!-- vimc: call SyntaxRange#Include('```sh', '```', 'sh', 'NonText'): -->
<!-- vim: set nospell iminsert=2: -->

### 快捷指南

```sh
docker run -it\
    -v OUTPUT_DIR:/data/dump\ # 挂载输出目录
    -v INPUT_DIR:/data/task_path\ # 挂载输入目录
    -p 127.0.0.1:5000:5000\ # 映射网络界面的端口
    --device /dev/kvm\ # 挂载内核虚拟化（Kernel-Based Virtual Machine, KVM）设备
    zdy023/mobile-env-web:latest\
    10.0.0.1 8081 "zdy023" www.wikihow.com www.example.com
```

几个参数：

1. 回放服务器的地址
2. 回放服务器的端口
3. 标注者的名字，用于保存的pickle文件名
4. 需要回放的域名

启动后，在浏览器里访问<http://127.0.0.1:5000>来打开标注界面。要关闭docker程序，在关掉网络界面后，在终端里按一次`Ctrl+C`即可。

输入目录（`INPUT_DIR`）的结构：

```
INPUT_DIR
├── tasks
│   ├── 180_on_a_scooter-8.textproto
│   ├── add_a_contact_on_whatsapp-8.textproto
│   ├── address_a_letter_to_england-7.textproto
│   └── ...
└── wikiHow_apkcombo.com.apk
```
