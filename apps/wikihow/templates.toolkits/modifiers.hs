module Modifiers
  ( regex_list
  , regex_esc
  , url_space
  )

import Data.List
  ( intercalate
  )
import qualified Network.URL as U

type Modifier = String -> String

regex_list :: Modifier
-- 将逗号隔开的关键词表转为可在正则表达式中使用的“或”连接的形式
regex_list x = "("
             ++ intercalate "|" (split ',' x)
             ++ ")"

regex_esc :: Modifier
-- 主要用于将输入中的“+”转义
regex_esc x = x >>= \c -> case c of
                            ' ' -> "\\\\+"
                            o -> [o]

split :: Char -> String -> [String]
split c [] = []
split c s = let (prfx, _:sffx) = break (== c) s
                rmns = split c sffx
            in case prfx of
                [] -> rmns
                p -> p:rmns

url_space :: Modifier
-- 将字符串按网址格式编码，如将空格替换为“+”等
url_space = map (\c -> case c of
                        ' ' -> '+'
                        o -> o)

url_title :: Modifier
-- 将题目转为网址中用“-”连接的形式
url_title = map (\c -> case c of
                        ' ' -> '-'
                        o -> o)

to_list :: Modifier
-- 将逗号分隔的关键词列表转为proto定义中的字符串列表
to_list x = "["
          ++ map (\s -> "\"" ++ "\"") (split ',' x)
          ++ "]"
