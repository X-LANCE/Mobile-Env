#!/usr/bin/python3

import uiautomator2
import time
import functools
import itertools

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
    time.sleep(2)
    with device.watch_context() as w:
        w.wait_stable()
def back():
    device.press("back")
    wait_for_stable()
def scroll_down():
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
    print("\x1b[34m#\x1b[0mClickable components: {:}".format(len(clickables)))
    for i, cpn in enumerate(clickables):
        #print(type(cpn))
        print("\x1b[34m{:}\x1b[0m {:}".format(i, component_to_str(cpn)))
    return clickables
    #  }}} function `print_clickables` # 
def special_components(is_search_page=False, has_search_box=False, has_option_button=False):
    #  function `special_components` {{{ # 
    """
    is_search_page - bool
    has_search_box - bool
    has_option_button - bool

    return tuple of two uiautomator2._selector.UiObject if not `has_search_box` and not `has_option_button`
      or tuple of four uiautomator2._selector.UiObject if `has_search_box` and not `has_option_button`
      or tuple of three uiautomator2._selector.UiObject if not `has_search_box` and `has_option_button`
      of tuple of five uiautomator2._selector.UiObject if `has_search_box` and `has_option_button`
    """

    results = [None, None, None, None, None]
    indices = [0]

    results[0] = device(clickable=True, className="android.widget.ImageView", description="Clear query" if is_search_page else "Search")
    results[3] = device(clickable=True, className="android.widget.ImageButton", descriptionContains="drawer")

    if has_search_box:
        results[1] = device(clickable=True, className=EDIT_TEXT_CLASS)
        results[2] = results[1].sibling(clickable=True, index=1)
        indices += [1, 2]
    indices.append(3)
    if has_option_button:
        results[4] = device(clickable=True, className="android.widget.ImageView", description="More options")
        indices.append(4)

    result = tuple(results[i] for i in indices)

    roman_digits = ["ⅰ", "ⅱ", "ⅲ", "ⅳ", "ⅴ"]
    for i, rslt in zip(roman_digits, result):
        print("\x1b[36m!{:}.\x1b[0m {:}".format(i, component_to_str(rslt)))

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
    author5_2 = author4.child(clickable=True, className=VIEW_CLASS, description="Author Info")
    return author5.exists or author5_2.exists
    #  }}} function `check_article` # 
#  }}} Functions to Check Page Class # 

def traverse_some_page(depth, depth_limit=5, scroll_depth=2,
        page_class="",
        is_search_page=False, has_search_box=False, has_option_button=False,
        get_more_special_components=(lambda: []),
        start_offset=0, is_valuable_to_click=(lambda _: True)):
    #  function `traverse_some_page` {{{ # 
    """
    depth - int
    depth_limit - int
    scroll_depth - int

    page_class - str

    is_search_page - bool
    has_search_box - bool
    has_option_button - bool

    get_more_special_components - callable returning list of uiautomator2._selector.UiObject

    start_offset - int
    is_valuable_to_click - callable accepting uiautomator2._selector.UiObject returning bool
    """

    counter = 0
    for d in range(scroll_depth+1):
        print("\x1b[5;31mTraversing {:} Page @d{:}...\x1b[0m".format(page_class, d))
        clickables = print_clickables()

        if d==0:
            special_component_list = special_components(is_search_page, has_search_box, has_option_button)
        else:
            special_component_list = special_components(is_search_page, has_option_button=has_option_button)

        more_special_component_list = get_more_special_components()
        more_special_component_list = list(filter(lambda cpn: cpn.exists, more_special_component_list))
        for i, cpn in enumerate(more_special_component_list):
            print("\x1b[36m!!{:}:\x1b[0m {:}".format(i, component_to_str(cpn)))

        for i, cpn in enumerate(clickables):
            if any(equal(cpn, spcl) for spcl in special_component_list) or\
                    any(equal(cpn, spcl) for spcl in more_special_component_list):
                print(i, component_to_str(cpn))
                continue
            if counter<start_offset:
                counter += 1
                continue
            if is_valuable_to_click(cpn):
                print("\x1b[1;33m{:}\x1b[0m".format(component_to_str(cpn)))
                cpn.click()
                traverse_page(depth+1, depth_limit=depth_limit)
        scroll_down()
        wait_for_stable()
    #  }}} function `traverse_some_page` # 

#  Functions to Traverse Pages of Specific Classes {{{ # 
def traverse_author_page(depth, depth_limit=5, scroll_depth=2):
    #  function `traverse_author_page` {{{ # 
    """
    depth - int
    depth_limit - int
    scroll_depth - int
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

    traverse_some_page(depth, depth_limit, scroll_depth,
        page_class="Author",
        get_more_special_components=more_special_components,
        start_offset=2)
    #  }}} function `traverse_author_page` # 
traverse_categories_page = functools.partial(traverse_some_page,
        page_class="Categories",
        is_search_page=False, has_search_box=False, has_option_button=False,
        get_more_special_components=(lambda: []),
        start_offset=0, is_valuable_to_click=is_category_item)
def traverse_category_page(depth, depth_limit=5, scroll_depth=2):
    #  function `traverse_category_page` {{{ # 
    """
    depth - int
    depth_limit - int
    scroll_depth - int
    """

    def more_special_components():
        #  function `more_special_components` {{{ # 
        """
        return list of uiautomator2._selector.UiObject
        """

        result_list = []

        title_view = device(resourceId="category_banner_title", className=VIEW_CLASS)
        if title_view.exists:
            title = title_view.info["text"]

            title_webview = device(text=title, className="android.webkit.WebView")
            view1 = title_webview.child(clickable=True, index=0, className=VIEW_CLASS)[0]
            view2 = view1.child(clickable=True, className=VIEW_CLASS, resourceId="mw-mf-page-center")

            result_list += [view1, view2]

        search_box = device(clickable=True, className=EDIT_TEXT_CLASS, resourceId="category_banner_search_input")
        if search_box.exists:
            search_button = search_box.sibling(clickable=True, className="android.widget.Button", resourceId="category_banner_submit")
            result_list += [search_box, search_button]

        cat_parent = device(clickable=True, className=VIEW_CLASS, resourceId="cat_parent", description="<")
        if cat_parent.exists:
            result_list.append(cat_parent)

        return result_list
        #  }}} function `more_special_components` # 

    traverse_some_page(depth, depth_limit, scroll_depth,
        page_class="Category",
        get_more_special_components=more_special_components)
    #  }}} function `traverse_category_page` # 
def traverse_article(depth, depth_limit=5, scroll_depth=2):
    #  function `traverse_article` {{{ # 
    """
    depth - int
    depth_limit - int
    scroll_depth - int
    """

    def more_special_components():
        #  function `more_special_components` {{{ # 
        """
        return list of uiautomator2._selector.UiObject
        """

        title_externel = device(clickable=True, resourceId="section_0", index=1,
                className=VIEW_CLASS, textStartsWith="How to ")
        title_internel = title_externel.child(clickable=True, className=VIEW_CLASS,
                descriptionStartsWith="How to ")

        author5_2 = None
        while True:
            author1 = device(className=VIEW_CLASS, resourceId="bodyContent", index=2)
            if not author1.exists:
                break
            author2 = author1.child(className=VIEW_CLASS, resourceId="intro")
            if not author2.exists:
                break
            author3 = author2.child(className=VIEW_CLASS, resourceId="coauthor_byline")
            if not author3.exists:
                break
            author4 = author3.child(className=VIEW_CLASS, resourceId="byline_info")
            if not author4.exists:
                break
            author5_2 = author4.child(clickable=True, className=VIEW_CLASS, description="Author Info")
            break

        trust_wikihow = device(clickable=True, className=VIEW_CLASS, description="Learn why people trust wikiHow")
        categories = device(clickable=True, className=VIEW_CLASS, description="CATEGORIES")
        approved = device(clickable=True, className="android.widget.Button", text="Approved")

        references = device(clickable=True, className="android.widget.Button",
                textStartsWith="Link to Reference",
                resourceIdMatches=r"^_ref-\d+$")
        return list(
                filter(lambda cpn: cpn is not None and cpn.exists,
                    [
                        title_externel, title_internel, author5_2,
                        trust_wikihow, categories, approved
                    ] + list(references)))
        #  }}} function `more_special_components` # 

    traverse_some_page(depth, depth_limit, scroll_depth,
        page_class="Article",
        has_option_button=True,
        get_more_special_components=more_special_components,
        is_valuable_to_click=(lambda cpn: not cpn.info["text"].startswith("Last Updated")))
    #  }}} function `traverse_article` # 
def traverse_other_page(depth, depth_limit=5, scroll_depth=2):
    #  function `traverse_other_page` {{{ # 
    """
    depth - int
    depth_limit - int
    scroll_depth - int
    """

    def more_special_components():
        #  function `more_special_components` {{{ # 
        """
        return list of uiautomator2._selector.UiObject
        """

        cat_parent = device(clickable=True, className=VIEW_CLASS,
                resourceId="cat_parent", description="<")

        return [cat_parent] if cat_parent.exists else []
        #  }}} function `more_special_components` # 

    traverse_some_page(depth, depth_limit, scroll_depth,
            page_class="\b",
            get_more_special_components=more_special_components,
            start_offset=2)
    #  }}} function `traverse_other_page` # 
#  }}} Functions to Traverse Pages of Specific Classes # 

def traverse_page(depth, depth_limit=5, scroll_depth=2):
    #  function `traverse_page` {{{ # 
    """
    depth - int
    depth_limit - int
    scroll_depth - int
    """

    wait_for_stable()
    if depth==depth_limit or device.app_current()["package"]!="com.wikihow.wikihowapp":
        print("\x1b[31mReturn Immediately\x1b[0m")
        back()
        return

    if check_author_page():
        traverse_author_page(depth, depth_limit=depth_limit, scroll_depth=2)
    elif check_categories_page():
        traverse_categories_page(depth, depth_limit=depth_limit, scroll_depth=2)
    elif check_category_page():
        traverse_category_page(depth, depth_limit=depth_limit, scroll_depth=2)
    elif check_article():
        traverse_article(depth, depth_limit=depth_limit, scroll_depth=2)
    else:
        traverse_other_page(depth, depth_limit=depth_limit, scroll_depth=2)

    # DEBUG
    print("\x1b[31mReturning\x1b[0m")
    back()
    #  }}} function `traverse_page` # 

def traverse_search_page(depth, depth_limit=2):
    #  function `traverse_search_page` {{{ # 
    """
    depth - int
    depth_limit - int
    """

    wait_for_stable()

    traverse_some_page(depth, depth_limit=depth_limit, scroll_depth=0,
            page_class="Search",
            is_search_page=True, has_search_box=True,
            start_offset=2)

    print("\x1b[31mReturning\x1b[0m")
    back()
    #  }}} function `traverse_search_page` # 

def traverse_main_page(depth_limit=5, scroll_depth=2):
    #  function `traverse_main_page` {{{ # 
    """
    depth_limit - int
    scroll_depth - int
    """

    #traverse_some_page(0, depth_limit=depth_limit, scroll_depth=scroll_depth,
        #page_class="Main",
        #has_search_box=True,
        #is_valuable_to_click=is_article_link)

    #  For Search Box .`android.widget.EditText` and Search Button .`android.widget.ImageView`~"Search" {{{ # 
    # TODO: search different keyword combinations
    #search_text = "How to clean a water dispenser"
    search_words = ["how to", "clean", "water", "dispenser"]
    search_texts = itertools.chain.from_iterable(
            map(lambda k: itertools.permutations(search_words, k),
                range(1, len(search_words)+1)))
    for t in search_texts:
        search_box = device(clickable=True, className=EDIT_TEXT_CLASS)
        search_box.click()
        device.set_fastinput_ime(True)
        device.send_keys(" ".join(t))
        device.set_fastinput_ime(False)
        device.send_action("search")
        traverse_search_page(1, depth_limit=2)
    #  }}} For Search Box .`android.widget.EditText` and Search Button .`android.widget.ImageView`~"Search" # 

    #  For Navigation Drawer .`android.widget.ImageButton`~+"drawer" {{{ # 
    # TODO: the last part to traverse
    # NOTE: Maybe manually
    #  }}} For Navigation Drawer .`android.widget.ImageButton`~+"drawer" # 
    #  }}} function `traverse_main_page` # 

if __name__ == "__main__":
    #traverse_main_page(depth_limit=4)
    traverse_page(3, depth_limit=4, scroll_depth=1)
