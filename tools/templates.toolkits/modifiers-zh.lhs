Copyright 2023 SJTU X-Lance Lab

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Created by Danyang Zhang @X-Lance.

> module Modifiers
>   ( to_list
>   , regex_list
>   , regex_esc
>   , url_title
>   , url_query
>   , url_title
>   , lower
>   , upper
>   , filter_comma
>   )
> 
> import Data.List
>   ( intercalate
>   , intersperse
>   )
> import qualified Network.URL as U
> 
> import Data.Char
>   ( toLower
>   , toUpper
>   , isAlphaNum
>   )
> 
> type Modifier = String -> String

###### 定义几个工具函数

该函数用于转义输入中的引号和反斜线，从而输出可以直接用在textproto中的字符串里。一般情况下，解析器会在最后自动执行该操作，该自动操作可以通过内置修饰符`no_quote`取消。

> escape :: String -> String
> escape x = x >>= \ch -> case ch of
>                           '"' -> "\\\""
>                           '\\' -> "\\\\"

这系列函数用于在特定位置切分字符串。

> splitBy' :: (Char -> Bool) -> String -> ([String], [String])
> splitBy :: (Char -> Bool) -> String -> [String]
> split :: Char -> String -> [String]
> splitBy' p [] = ([""], [])
> splitBy' p s = case break p s of
>                 (prfx, []) -> (prfx, [])
>                 (prfx, spl:sffx) -> let (rst, spls) = splitBy' p sffx
>                                     in (prfx:rst, spl:spls)
> splitBy p s = fst $ splitBy' p s
> split c = splitBy (== c)

###### 列表操作

该系列函数用于将输入的列表转为不同的形式用在目标文件中。

`to_list`用于将逗号分隔的关键词列表转为proto定义中的字符串列表，列表每项用`"`引住，各项间以", "分隔，总体以`[]`括住。各项中的引号等会自动转义，因此该修饰符应用后应通过`no_quote`取消自动的转义操作。

> to_list :: Modifier
> to_list x = "["
>           ++ (intercalate ", " $
>                 map (\s -> "\"" ++ s ++ "\"") $
>                 map escape $
>                 (split ',' x))
>           ++ "]"

`regex_list`将逗号隔开的关键词表转为可在正则表达式中使用的“或”连接的形式。该修饰符不会对每项中的正则保留符转义。

> regex_list :: Modifier
> regex_list x = "("
>              ++ intercalate "|" (split ',' x)
>              ++ ")"

`spacejoin`将逗号分隔的列表转为空格分隔的列表。

> spacejoin :: Modifier
> spacejoin = intersperse ' ' . split ','

###### 正则操作

`regex_esc`会将输入中的正则特殊字符转义。

> regex_esc :: Modifier
> regex_esc x = x >>= \c -> if c `elem` metaCharacters
>                           then ['\\', c]
>                           else [c]
>   where
>     metaCharacters = ".^$*+?{}\\[]|()"

###### 网址文本操作

> url_path :: Modifier
> url_query :: Modifier
> url_title :: Modifier

`url_path`按HTTP链接网址的路径段的规则编码输入字符串。

> url_path = U.encString False U.ok_path

`url_query`按HTTP链接网址中的请求段的规则编码输入字符串。

> url_query = U.encString True U.ok_param

`url_title`只做一件事：将所有空格替换为`-`。这通常用于在路径段编码文章题目、作者名等。

> url_title = map (\c -> case c of
>                         ' ' -> '-'
>                         o -> o)

###### 一般文本操作

这两个函数顾名思义，用于输入文本的大小写转换。

> lower :: Modifier
> upper :: Modifier
> lower = map toLower
> upper = map toUpper

`sentence_to_words`用于将一句话按空白字符分开，再用逗号串成列表。

> sentence_to_words :: Modifier
> sentence_to_words = intersperse ',' . words

###### 其他操作

`filter_comma`会删除输入中的所有`,`

> filter_comma :: Modifier
> filter_comma = filter (/= ',')

`remove_howto`会移除输入文本开头的"How to "，识别时不区分大小写。

> remove_howto :: Modifier
> remove_howto x@(h0:h1:h2:h3:h4:h5:h6:t) = if map toLower [h0, h1, h2, h3, h4, h5, h6] == "how to "
>                                           then t
>                                           else x
> remove_howto x = x
