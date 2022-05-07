#!/usr/bin/python3

import uiautomator2

def component_to_str(component):
    #  function `component_to_str` {{{ # 
    """
    component - uiautomator2._selector.UiObject

    return str
    """

    return ".{:}#{:}:{:}".format(
            component.info["className"],
            component.info["resourceName"],
            repr(component.info["contentDescription"]))
    #  }}} function `component_to_str` # 

PACKAGE_NAME = "com.wikihow.wikihowapp"
EDIT_TEXT_CLASS = "android.widget.EditText"
VIEW_CLASS = "android.view.View"

device = uiautomator2.connect()
device.app_wait(PACKAGE_NAME)
print(device.app_current())

def traverse_article():
    #  function `traverse_article` {{{ # 
    with device.watch_context() as w:
        w.wait_stable()
    device.press("back")
    #  }}} function `traverse_article` # 

def traverse_main_page():
    #  function `traverse_main_page` {{{ # 
    clickables = device(clickable=True)
    print("#Clickable components: {:}".format(len(clickables)))
    for i, cpn in enumerate(clickables):
        #print(type(cpn))
        print(i, component_to_str(cpn))

    #  For Search Box .`android.widget.EditText` and Search Button .`android.widget.ImageView`~"Search" {{{ # 
    # TODO: search different keyword combinations
    search_button1 = device(clickable=True, className="android.widget.ImageView", description="Search")
    search_box = device(clickable=True, className=EDIT_TEXT_CLASS)
    search_button2 = search_box.sibling(clickable=True, index=1)
    #  }}} For Search Box .`android.widget.EditText` and Search Button .`android.widget.ImageView`~"Search" # 

    menu_button = device(clickable=True, className="android.widget.ImageButton", descriptionContains="drawer")

    print("!", component_to_str(search_button1))
    print("!", component_to_str(search_box))
    print("!", component_to_str(search_button2))
    print("!", component_to_str(menu_button))

    for i, cpn in enumerate(clickables):
        if cpn==search_button1 or\
                cpn is search_box or\
                cpn is search_button2 or\
                cpn is menu_button:
            print(i, component_to_str(cpn))
        #print(component_to_str(cpn))
        #if cpn.info["className"]==VIEW_CLASS and cpn.info["contentDescription"].startswith("How to "):
            #cpn.click()
            #traverse_article()
        #else:
            #cpn.click()

    #  For Navigation Drawer .`android.widget.ImageButton`~+"drawer" {{{ # 
    # TODO: the last part to traverse
    #  }}} For Navigation Drawer .`android.widget.ImageButton`~+"drawer" # 
    #  }}} function `traverse_main_page` # 

if __name__ == "__main__":
    traverse_main_page()
