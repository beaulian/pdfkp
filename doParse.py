#-*- coding: utf-8 -*-
import os, re, sys
import multiprocessing
from collections import deque
from itertools import groupby
from bs4 import BeautifulSoup

def get_filename(_dir):
    pdf_dir = os.path.join(os.getcwd(), _dir)
    for path in os.listdir(pdf_dir):
        if not path.startswith(".") and path.endswith(".html"):
            yield os.path.join(pdf_dir, path)

def prepare_process(text, filter_tag="span"):
    regex = re.compile("".join(["</?", filter_tag, "[\s\S]*?>"]))
    return re.sub(regex, "", text)

def _suffix_debug(tag, regex):
    try:
        result = re.search(regex, " ".join(tag["class"])).group(1)
    except AttributeError:
        result = None
    finally:
        return result

_suffix = lambda tag, regex: re.search(regex, " ".join(tag["class"])).group(1)
_x = lambda tag: _suffix_debug(tag, "x(\S+)")
_h = lambda tag: _suffix_debug(tag, "h(\S+)")
_f = lambda tag: _suffix_debug(tag, "ff(\S+)")
_s = lambda tag: _suffix_debug(tag, "fs(\S+)")
_check_offset = lambda old_tag, tag: _x(old_tag) == _x(tag)
_check_height = lambda old_tag, tag: _h(old_tag) == _h(tag)
_check_font = lambda old_tag, tag: (_f(old_tag) == _f(tag)) and \
                                   (_s(old_tag) == _s(tag))

def end_process(tag):
    tags = deque([])
    for sibling in tag.previous_siblings:
        if _check_font(tag, sibling):
            tags.appendleft(sibling)
        else:
            break
        if not _check_offset(tag, sibling):
            break
    tags.append(tag)
    for sibling in tag.next_siblings:
        if not isinstance(sibling.string, basestring):
            continue
        if not _check_font(tag, sibling) or not _check_offset(tag, sibling):
            string = sibling.previous_sibling.string
            if isinstance(string, basestring) and \
                        re.search(u"。\s*$", string):
                break
        tags.append(sibling)

    return "".join(filter(lambda text: text != None,
                   map(lambda tag:tag.string, tags)))

def parse(keyword):
    with open(keyword+".txt", "w") as f1:
        for filename in get_filename("pdf/html"):
            with open(filename, "r") as f:
                soup = BeautifulSoup(prepare_process(f.read()), "html.parser")
                pre_results = soup.find_all("div", string=
                                            re.compile(unicode(keyword, "utf-8")))
                results = map(end_process, pre_results)
                if results:
                    f1.write(os.path.split(filename)[-1]+"\n")
                    f1.write("===========================================\n")
                    count = 1
                    for result, _ in groupby(results):
                        f1.write("结果"+str(count)+": "+result.encode("utf-8").strip()+"\")
                        count += 1
                    f1.write("\n")


if __name__ == '__main__':
    pool = multiprocessing.Pool(5)
    keywords = ["奖励", "保证金", "排污费", "绿化费", "在建工程"]
    for keyword in keywords:
        pool.apply_async(parse, (keyword, ))
    pool.close()
    pool.join()
