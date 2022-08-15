module Modifiers
  ( regex_list
  , regex_esc
  , url_space
  , url_title
  , to_list
  , lower
  , upper
  , title
  )

import Data.List
  ( intercalate
  )
import qualified Network.URL as U

import Data.Char
  ( toLower
  , toUpper
  , isAlphaNum
  )

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

splitBy' :: (Char -> Bool) -> String -> ([String], [String])
splitBy :: (Char -> Bool) -> String -> [String]
split :: Char -> String -> [String]
splitBy' p [] = ([], [])
splitBy' p s = case break p s of
                (prfx, []) -> (prfx, [])
                (prfx, spl:sffx) -> let (rst, spls) = splitBy' p sffx
                                    in (prfx:rst, spl:spls)
splitBy p s = fst $ splitBy' p s
split c = splitBy (== c)

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
          ++ (intercalate ", " $ map (\s -> "\"" ++ "\"") (split ',' x))
          ++ "]"

lower :: Modifier
upper :: Modifier
title :: Modifier
-- 转为小写
lower = map toLower
-- 转为大写
upper = map toUpper
-- 转为标题的首字母大写形式
title x = concat $ zipWith (++) words' symbols'
  where
    (words, symbols) = splitBy' (not . isAlphaNum) x

    symbols'
      | length symbols < length words = symbols ++ [""]
      | otherwise = symbols
    words' = map title' words

    title' [] = []
    title' h:t = toUpper h : lower t
