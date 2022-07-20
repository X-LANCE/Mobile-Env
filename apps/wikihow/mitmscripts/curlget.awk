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
    #post_set["/Special:SherlockController"] = 1;
}

{
    print($0)
    if(FNR<1097)
        next;

    command = "../classify_url.py \""$0"\""
    command | getline url_key;
    filename = "../headers/"urlkey_to_filename[url_key]".txt";
    close(command);

    last_path = gensub(/\//, "%2f", "g")
    if(length(last_path)>100)
        output_name = substr(last_path, 1, 100);
    else
        output_name = last_path;

    if(url_key=="/Special:SherlockController")
        next;
    if(url_key in post_set)
    {
        system("curl -i -A \"\" --output-dir test-mitmproxy --header @"filename" --request POST \"https://www.wikihow.com"$0"\" -o \""output_name"\"");
    }
    else
    {
        system("curl -i -A \"\" --output-dir test-mitmproxy --header @"filename" \"https://www.wikihow.com"$0"\" -o \""output_name"\"");
    }

    #if(NR==100)
        #exit;
    if(NR%100==0)
        system("sleep 10");
}
