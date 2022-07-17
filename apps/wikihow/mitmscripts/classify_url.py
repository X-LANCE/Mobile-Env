#!/usr/bin/python3

def classify(url: str) -> str:
    #  URL Classification {{{ # 
    if url.startswith("/x/collect?t="):
        if url[13:].startswith("first") or url[13:].startswith("later"):
            url_key = r"/x/collect\?t={first,later}&*"
        elif url[13:].startswith("exit") or url[13:].startswith("amp"):
            url_key = r"/x/collect\?t={exit,amp}&*"
        else:
            print("\x1b[1;31mClassification Error!\x1b[0m")
            raise ValueError("Unseen URL Pattern: {:}".format(url))
    elif url=="/x/zscsucgm?":
        url_key = r"/x/zscsucgm\?"
    elif url.startswith("/x/amp-view?"):
        url_key = r"/x/amp-view\?*"
    elif url.startswith("/ev/"):
        url_key = r"/ev/*"
    elif url.startswith("/load.php?"):
        if "only=styles" in url:
            url_key = r"/load.php\?*only=styles*"
        else:
            url_key = r"R /load.php?.\+$\(only=styles\)\@!"
    elif url.startswith("/video/"):
        url_key = r"/video/*"
    elif url=="/Special:SherlockController":
        url_key = r"/Special:SherlockController"
    elif url.startswith("/Special:RCWidget?"):
        url_key = r"/Special:RCWidget\?*"
    elif url.startswith("/extensions/wikihow/"):
        url_key = r"/extensions/wikihow/*"
    elif url.startswith("/images/"):
        url_key = r"/images/*"
    elif url.startswith("/skins/"):
        url_key = r"/skins/*"
    else:
        url_key = "[[:others:]]"

    return url_key
    #  }}} URL Classification # 

if __name__ == "__main__":
    import sys
    print(classify(sys.argv[1]))
