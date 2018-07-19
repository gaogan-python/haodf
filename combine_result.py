# -*- coding: utf-8 -*-
import json
import time
import sys
import os.path
from get_data import *
import re

def remove_crlf(s):
    r1 = u'[a-zA-Z0-9’!"#$%&\'()*+,-./:;<=>?@，。?★、…【】《》？“”‘’！[\\]^_`{|}●~]+'
    # r2 = u'[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F\u1C80-\u1C8F]+' # 俄文 西裏爾字母
    r2 = u'[\u0000-\u4dff\u9fa6-\uffff]+'
    s = s.replace('\r\n', ' ')
    s = s.replace('\n', '')
    s = re.sub(r1, ' ', s)
    s = re.sub(r2, ' ', s)

    #unicode chinese
    # re_words = re.compile(u"[\u4e00-\u9fa5]+")
    # s = re.findall(re_words, s)       # 查询出所有的匹配字符串
    return s.strip()

def main():
    download_map_file = 'data/download_map.json'
    download_map = {}
    total_article_txt = 'data/article_combine_result.txt'
    with open(download_map_file, 'r', encoding='utf8') as infile:
        download_map = json.load(infile)
    for key in download_map.keys():
        print('start main:%s'%(key))
        main_article_content_f = get_main_json_filename('data/main_article_file/', 'article', key)
        if(os.path.isfile(main_article_content_f)):
            main_article_content_json = ''
            with open(main_article_content_f, 'r', encoding='utf8') as infile:
                main_article_content_json = json.load(infile)
            if(not key in main_article_content_json.keys()):
                print('no main key: %s in %s' %(key, main_article_content_f))
                with open('com_no_main_key.txt', 'a') as the_file:
                    the_file.write(key+' not in '+main_article_content_f+'\n')
                continue
            else:
                inside_map = main_article_content_json[key]
                for i_key in inside_map.keys():
                    print('--start inside:%s'%(i_key))
                    article_content_list = main_article_content_json[key][i_key]
                    for article_content in article_content_list:
                        title = remove_crlf(article_content['title'])
                        content = remove_crlf(article_content['content'])
                        with open(total_article_txt, 'a') as the_file:
                            the_file.write(title+' '+content+'\n')
        else:
            print('no %s' % (main_article_content_f))

if __name__ == "__main__":
    main()