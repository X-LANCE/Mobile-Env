#!/usr/bin/python3

import uiautomator2
import time

def component_to_str(component):
    #  function `component_to_str` {{{ # 
    """
    component - uiautomator2._selector.UiObject

    return str
    """

    return ".{:}#{:}~{:}:{:}".format(
            component.info["className"],
            #component.info["index"],
            component.info["resourceName"],
            repr(component.info["contentDescription"]),
            repr(component.info["text"]))
    #  }}} function `component_to_str` # 

def equal(component1, component2):
    #  function `equal` {{{ # 
    """
    component1 - uiautomator2._selector.UiObject
    component2 - uiautomator2._selector.UiObject

    return bool
    """

    return component1.exists and component2.exists and\
            component1.info["className"]==component2.info["className"] and\
                (component1.info["contentDescription"]==component2.info["contentDescription"] or\
                    (component1.info["contentDescription"] is None or component1.info["contentDescription"]=="") and\
                        (component2.info["contentDescription"] is None or component2.info["contentDescription"]=="")) and\
                (component1.info["text"]==component2.info["text"] or\
                    (component1.info["text"] is None or component1.info["text"]=="") and\
                        (component2.info["text"] is None or component2.info["text"]==""))
    #  }}} function `equal` # 

PACKAGE_NAME = "com.wikihow.wikihowapp"
EDIT_TEXT_CLASS = "android.widget.EditText"
VIEW_CLASS = "android.view.View"

device = uiautomator2.connect()
device.app_wait(PACKAGE_NAME)
print(device.app_current())

def wait_for_stable():
    with device.watch_context() as w:
        w.wait_stable()
def roll_down():
    #  function `roll_down` {{{ # 
    device.swipe_ext("up")
    device.swipe_ext("up")
    #  }}} function `roll_down` # 

#  Functions w.r.t. Components {{{ # 
def print_clickables():
    #  function `print_clickables` {{{ # 
    """
    return uiautomator2._selector.UiObject
    """

    clickables = device(clickable=True)
    print("#Clickable components: {:}".format(len(clickables)))
    for i, cpn in enumerate(clickables):
        #print(type(cpn))
        print(i, component_to_str(cpn))
    return clickables
    #  }}} function `print_clickables` # 
def special_components(has_search_box=False, has_option_button=False):
    #  function `special_components` {{{ # 
    """
    has_search_box - bool
    has_option_button - bool

    return tuple of two uiautomator2._selector.UiObject if not `has_search_box` and not `has_option_button`
      or tuple of four uiautomator2._selector.UiObject if `has_search_box` and not `has_option_button`
      or tuple of three uiautomator2._selector.UiObject if not `has_search_box` and `has_option_button`
      of tuple of five uiautomator2._selector.UiObject if `has_search_box` and `has_option_button`
    """

    results = [None, None, None, None, None]
    indices = [0]

    results[0] = device(clickable=True, className="android.widget.ImageView", description="Search")
    results[3] = device(clickable=True, className="android.widget.ImageButton", descriptionContains="drawer")

    if has_search_box:
        results[1] = device(clickable=True, className=EDIT_TEXT_CLASS)
        results[2] = search_box.sibling(clickable=True, index=1)
        indices += [1, 2]
    indices.append(3)
    if has_option_button:
        results[4] = device(clickable=True, className="android.widget.ImageView", description="More options")
        indices.append(4)

    result = tuple(results[i] for i in indices)

    roman_digits = ["ⅰ", "ⅱ", "ⅲ", "ⅳ", "ⅴ"]
    for i, rslt in zip(roman_digits, result):
        print("!{:}. {:}".format(i, component_to_str(rslt)))

    return result
    #  }}} function `special_components` # 
def is_article_link(component):
    return component.info["className"]==VIEW_CLASS and component.info["contentDescription"].startswith("How to ")
def is_category_item(component):
    return len(component.info["contentDescription"])>0
#  }}} Functions w.r.t. Components # 

#  Functions to Check Page Class {{{ # 
def check_author_page():
    #  function `check_author_page` {{{ # 
    """
    return bool
    """

    author_website = device(resourceId="author_website", className=VIEW_CLASS, description="Website")
    if not author_website.exists:
        return False
    author_website2 = author_website.child(text="Website", className="android.widget.TextView")
    if not author_website2.exists:
        return False

    author_follow = device(resourceId="author_follow", className=VIEW_CLASS, description="+ Follow")
    author_follow2 = device(resourceId="author_follow_result", className=VIEW_CLASS, text="Coming Soon!")
    if author_follow.exists:
        is_author_page1 = author_follow.child(text="+ Follow", className="android.widget.TextView")
    return is_author_page1 or author_follow2.exists
    #  }}} function `check_author_page` # 
def check_categories_page():
    #  function `check_categories_page` {{{ # 
    """
    return bool
    """

    title = device(text="Categories", resourceId="section_0", className=VIEW_CLASS, index=0)
    if not title.exists:
        return False
    body = title.sibling(resourceId="bodyContent", className=VIEW_CLASS, index=1)
    if not body.exists:
        return False
    list_ = body.child(resourceId="catlist_container", className=VIEW_CLASS)
    if not list_.exists:
        return False
    list2 = list_.child(resourceId="catlist", className=VIEW_CLASS)
    return list2.exists
    #  }}} function `check_categories_page` # 
def check_category_page():
    #  function `check_category_page` {{{ # 
    """
    return bool
    """

    search_box = device(clickable=True, className=EDIT_TEXT_CLASS, resourceId="category_banner_search_input")
    if not search_box.exists:
        return False
    search_button = search_box.sibling(clickable=True, className="android.widget.Button", resourceId="category_banner_submit")
    return search_button.exists
    #  }}} function `check_category_page` # 
def check_article():
    #  function `check_article` {{{ # 
    """
    return bool
    """

    title_externel = device(clickable=True, resourceId="section_0", index=1,
            className=VIEW_CLASS, textStartsWith="How to ")
    if not title_externel.exists:
        return False
    title_internel = title_externel.child(clickable=True, className=VIEW_CLASS, descriptionStartsWith="How to ")
    if not title_internel.exists:
        return False
    author1 = device(className=VIEW_CLASS, resourceId="bodyContent", index=2)
    if not author1.exists:
        return False
    author2 = author1.child(className=VIEW_CLASS, resourceId="intro")
    if not author2.exists:
        return False
    author3 = author2.child(className=VIEW_CLASS, resourceId="coauthor_byline")
    if not author3.exists:
        return False
    author4 = author3.child(className=VIEW_CLASS, resourceId="byline_info")
    if not author4.exists:
        return False
    author5 = author4.child(clickable=True, className=VIEW_CLASS, index=2)
    return author5.exists
    #  }}} function `check_article` # 
#  }}} Functions to Check Page Class # 

def traverse_some_page(depth, depth_limit=5,
        page_class="",
        has_search_box=False, has_option_button=False,
        get_more_special_components=(lambda: []),
        start_offset=0, is_valuable_to_click=(lambda _: True)):
    #  function `traverse_some_page` {{{ # 
    """
    depth - int
    depth_limit - int

    page_class - str

    has_search_box - bool
    has_option_button - bool

    get_more_special_components - callable returning list of uiautomator2._selector.UiObject

    start_offset - int
    is_valuable_to_click - callable accepting uiautomator2._selector.UiObject returning bool
    """

    print("Traversing {:} Page...".format(page_class))
    clickables = print_clickables()

    special_component_list = special_components(has_search_box, has_option_button)

    more_special_component_list = get_more_special_components()
    for i, cpn in enumerate(more_special_component_list):
        print("!!{:}: {:}".format(i, component_to_str(cpn)))

    counter = 0
    for i, cpn in enumerate(clickables):
        if any(equal(cpn, spcl) for spcl in special_component_list) or\
                any(equal(cpn, spcl) for spcl in more_special_component_list):
            print(i, component_to_str(cpn))
            continue
        if counter<start_offset:
            counter += 1
            continue
        if is_valuable_to_click(cpn):
            cpn.click()
            traverse_page(depth+1, depth_limit=depth_limit)
    #  }}} function `traverse_some_page` # 

#  Functions to Traverse Pages of Specific Classes {{{ # 
def traverse_author_page(depth, depth_limit=depth_limit):
    #  function `traverse_author_page` {{{ # 
    """
    depth - int
    depth_limit - int
    """

    def more_special_components():
        #  function `more_special_components` {{{ # 
        """
        return list of uiautomator2._selector.UiObject
        """

        author_website = device(resourceId="author_website", className=VIEW_CLASS,
                description="Website", clickable=True)
        author_follow = device(resourceId="author_follow", className=VIEW_CLASS,
                description="+ Follow", clickable=True)
        author_social = device(resourceId="author_social", className=VIEW_CLASS)
        author_socials = author_social.child(clickable=True)
        return [author_website, author_follow] + list(author_socials)
        #  }}} function `more_special_components` # 

    traverse_some_page(depth, depth_limit,
        page_class="Author",
        get_more_special_components=more_special_components,
        start_offset=2)
    #  }}} function `traverse_author_page` # 
#  }}} Functions to Traverse Pages of Specific Classes # 

def traverse_author_page(depth, depth_limit=5):
    #  function `traverse_author_page` {{{ # 
    print("Traversing Author Page")
    clickables = print_clickables()

    search_button1,\
        menu_button = special_components()

    author_website = device(resourceId="author_website", className=VIEW_CLASS, description="Website", clickable=True)
    author_follow = device(resourceId="author_follow", className=VIEW_CLASS, description="+ Follow", clickable=True)
    author_social = device(resourceId="author_social", className=VIEW_CLASS)
    author_socials = author_social.child(clickable=True)
    for i, cpn in enumerate(author_socials):
        print("!!{:}: {:}".format(i, component_to_str(cpn)))

    counter = 0
    for i, cpn in enumerate(clickables):
        if equal(cpn, search_button1) or\
                equal(cpn, menu_button) or\
                equal(cpn, author_website) or\
                equal(cpn, author_follow) or\
                any(equal(cpn, scl) for scl in author_socials):
            print(i, component_to_str(cpn))
            continue
        print(component_to_str(cpn))
        if counter<2:
            counter += 1
            continue
        cpn.click()
        traverse_page(depth+1, depth_limit=depth_limit)
    #  }}} function `traverse_author_page` # 
def traverse_categories_page(depth, depth_limit=5):
    #  function `traverse_categories_page` {{{ # 
    print("Traversing Categories Page")
    clickables = print_clickables()

    search_button1,\
        menu_button = special_components()

    for i, cpn in enumerate(clickables):
        if equal(cpn, search_button1) or\
                equal(cpn, menu_button):
            print(i, component_to_str(cpn))
            continue
        if is_category_item(cpn):
            cpn.click()
            traverse_page(depth+1, depth_limit=depth_limit)
    #  }}} function `traverse_categories_page` # 
def traverse_category_page(depth, depth_limit=5):
    #  function `traverse_category_page` {{{ # 
    print("Traversing Category Page")

    clickables = print_clickables()

    search_button1,\
        menu_button = special_components()

    title_view = device(resourceId="category_banner_title", className=VIEW_CLASS)
    title = title_view.info["text"]

    title_webview = device(text=title, className="android.webkit.WebView")
    view1 = title_webview.child(clickable=True, index=0, className=VIEW_CLASS)[0]
    view2 = view1.child(clickable=True, className=VIEW_CLASS, resourceId="mw-mf-page-center")

    search_box = device(clickable=True, className=EDIT_TEXT_CLASS, resourceId="category_banner_search_input")
    search_button = search_box.sibling(clickable=True, className="android.widget.Button", resourceId="category_banner_submit")

    cat_parent = device(clickable=True, className=VIEW_CLASS, resourceId="cat_parent", description="<")
    print("!!₁. {:}".format(component_to_str(search_box)))
    print("!!₂. {:}".format(component_to_str(search_button)))
    print("!!₃. {:}".format(component_to_str(view1)))
    print("!!₄. {:}".format(component_to_str(view2)))
    print("!!₅. {:}".format(component_to_str(cat_parent)))

    for i, cpn in enumerate(clickables):
        if equal(cpn, search_button1) or\
                equal(cpn, menu_button) or\
                equal(cpn, search_box) or\
                equal(cpn, search_button) or\
                equal(cpn, view1) or\
                equal(cpn, view2) or\
                equal(cpn, cat_parent):
            print(i, component_to_str(cpn))
            continue
        print(component_to_str(cpn))
        cpn.click()
        traverse_page(depth+1, depth_limit=depth_limit)
    #  }}} function `traverse_category_page` # 
def traverse_article(depth, depth_limit=5):
    #  function `traverse_article` {{{ # 
    print("Traversing Article")

    clickables = print_clickables()

    search_button1,\
        menu_button,\
        option_button = special_components(has_option_button=True)

    title_externel = device(clickable=True, resourceId="section_0", index=1,
            className=VIEW_CLASS, textStartsWith="How to ")
    title_internel = title_externel.child(clickable=True, className=VIEW_CLASS, descriptionStartsWith="How to ")
    #author = device(className=VIEW_CLASS, resourceId="bodyContent", index=2)\
            #.child(className=VIEW_CLASS, resourceId="intro")\
            #.child(className=VIEW_CLASS, resourceId="coauthor_byline")\
            #.child(className=VIEW_CLASS, resourceId="byline_info")\
            #.child(clickable=True, className=VIEW_CLASS, index=2)
    print("!!₁. {:}".format(component_to_str(title_externel)))
    print("!!₂. {:}".format(component_to_str(title_internel)))
    #print("!!₃. {:}".format(component_to_str(author)))

    for i, cpn in enumerate(clickables):
        if equal(cpn, search_button1) or\
                equal(cpn, menu_button) or\
                equal(cpn, option_button) or\
                equal(cpn, title_externel) or\
                equal(cpn, title_internel):
            print(i, component_to_str(cpn))
            continue
        if cpn.info["text"].startswith("Last Updated"):
            continue
        print(component_to_str(cpn))
        cpn.click()
        traverse_page(depth+1, depth_limit=depth_limit)
    #  }}} function `traverse_article` # 

def traverse_page(depth, depth_limit=5):
    #  function `traverse_page` {{{ # 
    """
    depth - int
    depth_limit - int
    """

    time.sleep(2)
    wait_for_stable()
    if depth==depth_limit:
        device.press("back")
        time.sleep(2)
        wait_for_stable()
        return

    if check_author_page():
        traverse_author_page(depth, depth_limit=depth_limit)
    elif check_categories_page():
        traverse_categories_page(depth, depth_limit=depth_limit)
    elif check_category_page():
        traverse_category_page(depth, depth_limit=depth_limit)
    elif check_article():
        traverse_article(depth, depth_limit=depth_limit)
    else:
        print("Traversing Page")
        clickables = print_clickables()

        search_button1,\
            menu_button = special_components()

        cat_parent = device(clickable=True, className=VIEW_CLASS, resourceId="cat_parent", description="<")

        for i, cpn in enumerate(clickables):
            if equal(cpn, search_button1) or\
                    equal(cpn, menu_button):
                print(i, component_to_str(cpn))
                continue
            if cat_parent.exists and equal(cpn, cat_parent):
                print(i, component_to_str(cpn))
                continue
            print(component_to_str(cpn))
            cpn.click()
            traverse_page(depth+1, depth_limit=depth_limit)

    # DEBUG
    #device.press("back")
    #time.sleep(2)
    #wait_for_stable()
    #  }}} function `traverse_page` # 

def traverse_main_page(depth_limit=5):
    #  function `traverse_main_page` {{{ # 
    """
    depth_limit - int
    """

    print("Traversing Main Page")
    clickables = print_clickables()

    #  For Search Box .`android.widget.EditText` and Search Button .`android.widget.ImageView`~"Search" {{{ # 
    # TODO: search different keyword combinations
    #search_button1 = device(clickable=True, className="android.widget.ImageView", description="Search")
    #search_box = device(clickable=True, className=EDIT_TEXT_CLASS)
    #search_button2 = search_box.sibling(clickable=True, index=1)
    #  }}} For Search Box .`android.widget.EditText` and Search Button .`android.widget.ImageView`~"Search" # 

    #menu_button = device(clickable=True, className="android.widget.ImageButton", descriptionContains="drawer")

    #print("!ⅰ", component_to_str(search_button1))
    #print("!ⅱ", component_to_str(search_box))
    #print("!ⅲ", component_to_str(search_button2))
    #print("!ⅳ", component_to_str(menu_button))
    search_button1,\
        search_box,\
        search_button2,\
        menu_button = special_components(has_search_box=True)

    for i, cpn in enumerate(clickables):
        if equal(cpn, search_button1) or\
                equal(cpn, search_box) or\
                equal(cpn, search_button2) or\
                equal(cpn, menu_button):
            print(i, component_to_str(cpn))
            continue
        print(component_to_str(cpn))
        if is_article_link(cpn):
            cpn.click()
            traverse_page(1, depth_limit=depth_limit)
        #else:
            #cpn.click()

    #  For Navigation Drawer .`android.widget.ImageButton`~+"drawer" {{{ # 
    # TODO: the last part to traverse
    #  }}} For Navigation Drawer .`android.widget.ImageButton`~+"drawer" # 
    #  }}} function `traverse_main_page` # 

if __name__ == "__main__":
    #traverse_main_page()
    #traverse_article(1, depth_limit=2)
    #traverse_page(1, depth_limit=2)
    roll_down()
