# -*- coding: utf-8 -*-
"""newick — 极简 Newick 树解析/生成（本 skill 自带，替代原库 helpers/newick.py）。

接口（按 case_seg012–015 配方所需）：
  parse_newick(s) -> Node          解析 newick 字符串
  random_newick(n_leaves, seed=None) -> str   生成 n 叶随机树（balanced binary 递归）
  Node: .name .children .length;  is_leaf();  iter_leaf_depth();  leaves()
"""
from __future__ import annotations
import random

class Node(dict):
    """dict 风格节点：nd['name'] / nd['children'] / nd['length'] 可下标访问，
    同时保留 .name/.children 属性与 is_leaf()/leaves() 方法。"""

    def __init__(self, name="", children=None, length=0.0):
        super().__init__(name=name, children=children or [], length=length)

    @property
    def name(self): return self["name"]
    @property
    def children(self): return self["children"]
    @property
    def length(self): return self["length"]

    def is_leaf(self):
        return not self["children"]

    def leaves(self):
        out = []
        def rec(n):
            if n.is_leaf(): out.append(n)
            for c in n["children"]: rec(c)
        rec(self); return out

    def iter_leaf_depth(self):
        def rec(n, d):
            if n.is_leaf(): yield (n, d)
            for c in n["children"]: yield from rec(c, d + 1)
        yield from rec(self, 0)

def _tokenize(s):
    return list(s.strip().rstrip(";"))

def parse_newick(s: str) -> Node:
    toks = _tokenize(s)
    pos = 0
    def parse_node():
        nonlocal pos
        children = []
        name = ""
        if toks[pos] == "(":
            pos += 1
            while True:
                children.append(parse_node())
                if toks[pos] == ",":
                    pos += 1; continue
                if toks[pos] == ")":
                    pos += 1; break
            # 可能跟内部节点名
            while pos < len(toks) and toks[pos] not in ",()":
                name += toks[pos]; pos += 1
        else:
            while pos < len(toks) and toks[pos] not in ",()":
                name += toks[pos]; pos += 1
        length = 0.0
        if pos < len(toks) and toks[pos] == ":":
            pos += 1
            num = ""
            while pos < len(toks) and toks[pos] not in ",()":
                num += toks[pos]; pos += 1
            try: length = float(num)
            except ValueError: length = 0.0
        return Node(name=name, children=children, length=length)
    return parse_node()

def random_newick(n_leaves: int, seed=None) -> str:
    rng = random.Random(seed)
    leaves = [f"sp{i:03d}" for i in range(n_leaves)]
    rng.shuffle(leaves)
    def build(names):
        if len(names) == 1:
            return names[0], 1.0
        cut = rng.randint(1, len(names) - 1)
        left, dl = build(names[:cut])
        right, dr = build(names[cut:])
        bl = round(rng.uniform(0.02, 0.2), 4)
        return f"({left}:{dl},{right}:{dr})", bl
    body, _ = build(leaves)
    return body + ";"
