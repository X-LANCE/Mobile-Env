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

###### Define Several Tool Functions

This function is used to escape the quotation marks and backslashes in the input, so that the transormed input can be directly inserted into the textproto strings. The parser will invoke this operation automatically by default unless it is canceled by the built-in modifier `no_quote`.

> escape :: String -> String
> escape x = x >>= \ch -> case ch of
>                           '"' -> "\\\""
>                           '\\' -> "\\\\"

This group of functions will split the string at some specific positions.

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

###### List Operations

This category of functions are used to convert the list in the input to different formats.

`to_list` transforms the comma-separated keywords list into the string list in the proto definition. Each list item will be quoted by `"` and separated by ", ". The whole list will be bracked by `[]`。The quotation marks in the items will be escaped automatically, thus, `no_quote` should be applied after this modifier to cancel the built-in escaping.

> to_list :: Modifier
> to_list x = "["
>           ++ (intercalate ", " $
>                 map (\s -> "\"" ++ s ++ "\"") $
>                 map escape $
>                 (split ',' x))
>           ++ "]"

`regex_list` transforms the comma-separated keywords list into the "or"-connected format which can be used in the regex. Note that this modifier will not escape the reserved symbols of the regex.

> regex_list :: Modifier
> regex_list x = "("
>              ++ intercalate "|" (split ',' x)
>              ++ ")"

`spacejoin` converts a comma-seperated list into a space-seperated list.

> spacejoin :: Modifier
> spacejoin x = intersperse ' ' (split ',' x)

###### Regex Operations

`regex_esc` escapes the special regex characters in the input.

> regex_esc :: Modifier
> regex_esc x = x >>= \c -> if c `elem` metaCharacters
>                           then ['\\', c]
>                           else [c]
>   where
>     metaCharacters = ".^$*+?{}\\[]|()"

###### URL Text Operations

> url_path :: Modifier
> url_query :: Modifier
> url_title :: Modifier

`url_path` encodes the input string according to the rule of the path segment of HTTP URL.

> url_path = U.encString False U.ok_path

`url_query` encodes the input string according to the rule of the query segment of HTTP URL.

> url_query = U.encString True U.ok_param

The only thing `url_title` does is to replace all the white spaces with `-`. This operation is always adopted in the path segments to encode the article titles, the author names, *etc*.

> url_title = map (\c -> case c of
>                         ' ' -> '-'
>                         o -> o)

###### Commen Text Operations

These two functions are used for case conversion of the input text just as their names.

> lower :: Modifier
> upper :: Modifier
> lower = map toLower
> upper = map toUpper

###### Other Operations

`filter_comma` will delete all the `,` in the input.

> filter_comma :: Modifier
> filter_comma = filter (/= ',')

`remove_howto` removes the leading "How to " in the input text. The matching is case-insensitive.

> remove_howto :: Modifier
> remove_howto x@(h0:h1:h2:h3:h4:h5:h6:t) = if map toLower [h0, h1, h2, h3, h4, h5, h6] == "how to "
>                                           then t
>                                           else x
> remove_howto x = x
