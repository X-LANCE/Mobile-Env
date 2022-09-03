#!/usr/bin/python3

import yaml
import numpy as np
import os.path
import urllib.parse

with open("../mitmscripts/article.info.yaml") as f:
    article_infos = yaml.load(f, yaml.Loader)
    article_data = {info["title"]: info for info in article_infos}
with open("../mitmscripts/author.info.yaml") as f:
    author_infos = yaml.load(f, yaml.Loader)
    author_data = {info["author"]: info for info in author_infos}
with open("../mitmscripts/categ.info.yaml") as f:
    categ_infos = yaml.load(f, yaml.Loader)
    categ_data = {info["categ"]: info for info in categ_infos}

instance_path = "../templates.autoinstances"

def encode_name(title: str, space: str = "_", percent: bool = True) -> str:
    title = title.replace(",", "").replace("/", " or ").replace(" ", space)
    title = urllib.parse.quote_plus(title)
    if percent:
        title = title.replace("%", "P")
    return title

# actions on article page
# + about_page
# + rate_no
# + rate_yes
# + share
# + author_page
# + bookmark
# + category_page
# + reference
# + no succeeders

prototype_steps = [ "about_page-prototype"
                  , "rate_no-prototype"
                  , "rate_yes-prototype"
                  , "share-prototype"
                  ]

#  List Sample {{{ # 
nb_article_tasks = len(article_infos)*9
#nb_author_tasks = len(author_infos)
#nb_categ_tasks = len(categ_infos)
nb_tasks = nb_article_tasks
target_nb_tasks = 1_0000

rng = np.random.default_rng()
indices = rng.permutation(nb_tasks)[:target_nb_tasks]
for i in indices:
    i_ = i//9
    act = i%9

    info = article_infos[i_]

    # 1. search and access article
    name = encode_name(info["title"].lower())
    search_step = "search-{:}".format(name)
    article_step = "article-{:}".format(name)
    task_file = "{:}\n{:}\n".format(search_step, article_step)
    search_conf = os.path.join(instance_path, search_step + ".conf")
    if not os.path.exists(search_conf):
        with open(search_conf, "w") as f:
            f.write("vocabulary: {:}\n".format(",".join(["how to"] + info["keywords"])))
            f.write("name: {:}\n".format(name))
            f.write("command: {:}\n".format("how to " + info["title"].lower()))
            f.write("keywords: {:}\n".format(",".join(info["keywords"])))
    article_conf = os.path.join(instance_path, article_step + ".conf")
    if not os.path.exists(article_conf):
        with open(article_conf, "w") as f:
            f.write("title: {:}\n".format(info["title"]))

    # 2. suceeding step
    if act<4:
        task_file += prototype_steps[act] + "\n"
    elif act==4 and len(info["authors"])>0:
        author = info["authors"][rng.integers(len(info["authors"]))]
        author_page_step = "author_page-{:}".format(encode_name(author.lower()))
        task_file += author_page_step + "\n"
        author_page_conf = os.path.join(instance_path, author_page_step + ".conf")
        if not os.path.exists(author_page_conf):
            with open(author_page_conf, "w") as f:
                f.write("author: {:}\n".format(author))

        # succeeds further
        if rng.integers(2)==1:
            article_list = author_data[encode_name(author, space="-", percent=False)]["articles"]
            last_article = article_list[rng.integers(len(article_list))]
            if last_article!=info["title"]:
                last_name = encode_name(last_article.lower())
                last_article_step = "article-{:}".format(last_name)
                task_file += last_article_step + "\n"
                last_article_conf = os.path.join(instance_path, last_article_step + ".conf")
                if not os.path.exists(last_article_conf):
                    with open(last_article_conf, "w") as f:
                        f.write("title: {:}\n".format(last_article))
    elif act==5:
        bookmark_step = "bookmark-{:}".format(name)
        task_file += bookmark_step + "\n"
        bookmark_conf = os.path.join(instance_path, bookmark_step + ".conf")
        if not os.path.exists(bookmark_conf):
            with open(bookmark_conf, "w") as f:
                f.write("title: {:}\n".format(info["title"]))
    elif act==6 and len(info["categs"])>0:
        categ = info["categs"][rng.integers(len(info["categs"]))]
        category_page_step = "category_page-{:}".format(encode_name(categ.lower()))
        task_file += category_page_step + "\n"
        category_page_conf = os.path.join(instance_path, category_page_step + ".conf")
        if not os.path.exists(category_page_conf):
            with open(category_page_conf, "w") as f:
                f.write("categ: {:}\n".format(categ))

        if rng.integers(2)==1:
            article_list = categ_data[encode_name(categ, space="-", percent=False)]["articles"]
            last_article = article_list[rng.integers(len(article_list))]
            if last_article!=info["title"]:
                last_name = encode_name(last_article.lower())
                last_article_step = "article-{:}".format(last_name)
                task_file += last_article_step + "\n"
                last_article_conf = os.path.join(instance_path, last_article_step + ".conf")
                if not os.path.exists(last_article_conf):
                    with open(last_article_conf, "w") as f:
                        f.write("title: {:}\n".format(last_article))
    elif act==7:
        reference_step = "reference-{:}".format(name)
        task_file += reference_step + "\n"
        reference_conf = os.path.join(instance_path, reference_step + ".conf")
        if not os.path.exists(reference_conf):
            with open(reference_conf, "w") as f:
                f.write("title: {:}\n".format(info["title"]))

    with open(os.path.join(instance_path, "{:}-{:}.task".format(name, act)), "w") as f:
        f.write(task_file)
#  }}} List Sample # 

#  Category Listing Page {{{ # 
category_list = [ "Arts and Entertainment"
                , "Cars & Other Vehicles"
                , "Computers and Electronics"
                , "Education and Communications"
                , "Family Life"
                , "Finance and Business"
                , "Food and Entertaining"
                , "Health"
                , "Hobbies and Crafts"
                , "Holidays and Traditions"
                , "Home and Garden"
                , "Personal Care and Style"
                , "Pets and Animals"
                , "Philosophy and Religion"
                , "Relationships"
                , "Sports and Fitness"
                , "Travel"
                , "Work World"
                , "Youth"
                ]
categ = category_list[rng.integers(len(category_list))]
category_list_step = "category_list-prototype"
category_page_step = "category_page-{:}".format(encode_name(categ.lower()))
task_file = "{:}\n{:}\n".format(category_list_step, category_page_step)
category_page_conf = os.path.join(instance_path, category_page_step + ".conf")
if not os.path.exists(category_page_conf):
    with open(category_page_conf, "w") as f:
        f.write("categ: {:}\n".format(categ))

article_list = categ_data[encode_name(categ, space="-", percent=False)]["articles"]
article_title = article_list[rng.integers(len(article_list))]
name = encode_name(article_title.lower())
article_step = "article-{:}".format(name)
task_file += article_step + "\n"
article_conf = os.path.join(instance_path, article_conf + ".conf")
if not os.path.exists(article_conf):
    with open(article_conf, "w") as f:
        f.write("title: {:}\n".format(article_title))

with open(os.path.join(instance_path, "{:}-{:}.task".format(encode_name(categ.lower()), name)), "w") as f:
    f.write(task_file)
#  }}} Category Listing Page # 
