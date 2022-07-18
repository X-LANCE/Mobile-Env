#!/usr/bin/gawk -f

BEGIN {
    urlkey_to_filename["[[:others:]]"] = "others";
    urlkey_to_filename["/x/collect\\?t={first,later}&*"] = "collect-fl";
    urlkey_to_filename["/x/zscsucgm\\?"] = "zscsucgm";
    urlkey_to_filename["/x/collect\\?t={exit,amp}&*"] = "collect-ea";
    urlkey_to_filename["/x/amp-view\\?*"] = "amp-view";
    urlkey_to_filename["/ev/*"] = "ev";
    urlkey_to_filename["R /load.php?.\\+$\\(only=styles\\)\\@!"] = "load";
    urlkey_to_filename["/video/*"] = "video";
    urlkey_to_filename["/Special:SherlockController"] = "SherlockController";
    urlkey_to_filename["/Special:RCWidget\\?*"] = "RCWidget";
    urlkey_to_filename["/load.php\\?*only=styles*"] = "load-style";
    urlkey_to_filename["/extensions/wikihow/*"] = "extensions";
    urlkey_to_filename["/images/*"] = "images";
    urlkey_to_filename["/skins/*"] = "skins";

    post_set["/x/collect\\?t={exit,amp}&*"] = 1;
    post_set["/x/amp-view\\?*"] = 1;
    post_set["/Special:SherlockController"] = 1;
}

{
    "./classify_url.py \""$0"\"" | getline url_key;
    filename = "headers/"urlkey_to_filename[url_key]".txt";

    if(url_key in post_set)
    {
        system("curl --remote-name --header @"filename" --request POST \"https://www.wikihow.com"$0"\"");
    }
    else
    {
        system("curl --remote-name --header @"filename" \"https://www.wikihow.com"$0"\"");
    }
}
