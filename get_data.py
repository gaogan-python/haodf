# -*- coding: utf-8 -*-
import json
import requests
import time
from bs4 import BeautifulSoup

main_href = 'https://www.haodf.com'
def connect_method(target_url):
    timeout = 10
    sleep_t = 0.5
    # cookie = {
    #         'BAIDUID': '670C617B3C5595EE1287EC8806E2481A:FG=1',
    #         'BAIDU_SSP_lcr': 'http://health.sina.com.cn/',
    #         'BAIDU_WISE_UID': 'wapp_1531727366212_580',
    #         'CNZZDATA1256706712': '1506524558-1531726801-null%7C1531795311',
    #         'CNZZDATA1914877': 'cnzz_eid%3D595821711-1531726552-https%253A%252F%252Fwww.haodf.com%252F%26ntime%3D1531731907',
    #         'HMACCOUNT': 'DCFD23BB079CCC12',
    #         'HMVT': '1057fce5375b76705b65338cc0397720|1531728498|',
    #         'Hm_lpvt_dfa5478034171cc641b1639b2a5b717d': '1531796600',
    #         'Hm_lvt_dfa5478034171cc641b1639b2a5b717d': '1531727954',
    #         'UM_distinctid': '164a219be05822-077b5fad6e02d2-16386952-13c680-164a219be07356',
    #         '__jsluid': 'cc79b4598cbeb1f6f9ba91700dc6c7e3',
    #         '_ga': 'GA1.2.424697366.1531727954',
    #         '_gid': 'GA1.2.2109754063.1531727954',
    #         'atpsida': '4d75a42a05b4d7f8ec9a52ea_1531736682_1',
    #         'atpsida': '34b8a2235ebf39b6c6fdf678_1531796598_1',
    #         'cad': '3rAZ+snrQENLkXCLgkzN4MBDO5TEFVggPSXJlsNscCM=0001',
    #         'cap': '4e5d',
    #         'cna': 'eO+fE2VGJWgCAdyHV0iebzMy',
    #         'g': '20124_1531727952424',
    #         'pgv_pvi': '337737728',
    #         'pgv_si': 's6239664128',
    #         'sca': 'c14a5116',
    #         'yunpk': '5379512461380173',
    #         }
    header = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36",
            'Content-Type': 'text/html',
            'Connection': 'keep-alive'
            }
    try:
        resp = requests.get(
            url = target_url, timeout=timeout, verify=True, headers=header #, cookies=cookie
        )
    except requests.exceptions.ReadTimeout:
        print('timeout, sleep 10 sec')
        time.sleep(10)
        resp = requests.get(
            url = target_url, timeout=timeout, verify=True, headers=header #, cookies=cookie
        )

    if resp.status_code != 200:
        print(resp)
        print(resp.request.headers)
        print(resp.headers)
        print('invalid url:', resp.url)
        time.sleep(sleep_t)
        return False
    else:
        return resp
def get_main_map(target_url):
    resp = connect_method(target_url)
    result_map = {}
    if resp:
        soup = BeautifulSoup(resp.text, 'html.parser')
        divs = soup.find_all("div", {"class": "kstl"})
        for e_div in divs:
            e_div_a = e_div.findChildren()[0]
            result_map[e_div_a.text] = main_href+e_div_a['href']
        return result_map
    else:
        return False
def get_inside_map(target_url):
    resp = connect_method(target_url)
    result_map = {}
    if resp:
        soup = BeautifulSoup(resp.text, 'html.parser')
        targets = soup.select("div#el_result_content div.ct li a")
        for target in targets:
            result_map[target.text] = main_href+target['href']
        return result_map
    else:
        return False
def download_map2json(json_name):
    target_url = main_href+'/jibing/xiaoerke/list.htm'
    main_map = get_main_map(target_url)
    download_map = {}
    if not main_map:
        print('something wrong')
    for key in main_map.keys():
        inside_href = main_map[key]
        inside_map = get_inside_map(inside_href)
        download_map[key] = inside_map
    with open(json_name, 'w') as outfile:
        json.dump(download_map, outfile)
def get_total_page(t_href):
    t_href = t_href + '/wz_0_0_1.htm'
    resp = connect_method(t_href)
    if(resp):
        total_page = 1
        soup = BeautifulSoup(resp.text, 'html.parser')
        page_num_t = soup.select("font.black.pl5.pr5")
        if page_num_t:
            total_page = int(page_num_t[0].text)
        return total_page
    else:
        return False
def get_article_list(page_href):
    retry_times = 0
    while(retry_times < 3):
        resp = connect_method(page_href)
        content_links = []
        if(resp):
            soup = BeautifulSoup(resp.text, 'html.parser')
            select_links = soup.select("div.dis_article h2 a")
            for select_link in select_links:
                content_links.append('https:'+select_link['href'])
            return content_links
        else:
            print('retry %d times, href: %s' % (retry_times, page_href))
            retry_times = retry_times + 1
    return False
def get_article_from_download_map(json_name, o_json_name, countinue_main, countinue_inside):
    download_map = {}
    article_link_map = {}
    start_download_flag = False
    with open(json_name, 'r') as infile:
        download_map = json.load(infile)
    for key in download_map.keys():
        inside_map = download_map[key]
        article_link_map[key] = {}
        print('start main:%s'%(key))
        for i_key in inside_map.keys():
            t_href = inside_map[i_key]
            if (not start_download_flag) and (key == countinue_main) and (i_key == countinue_inside):
                start_download_flag = True
            if start_download_flag:
                print('--start inside:%s, href:%s'%(i_key,t_href))
                t_href = t_href[:t_href.rfind('.')] # remove '.htm'
                total_page = get_total_page(t_href)
                print('total_page: %d' %(total_page))
                content_links = []
                for page_i in range(total_page):
                    page_href = t_href + '/wz_0_0_' + str(page_i+1) + '.htm'
                    print(page_href)
                    tmp = get_article_list(page_href)
                    if(tmp):
                        print('Get %d article links.' % (len(tmp)))
                        content_links.extend(tmp)
                    else:
                        print('fail, write href to txt')
                        with open('failhref_file.txt', 'a') as the_file:
                            the_file.write(page_href+'\n')
                    #break
                article_link_map[key][i_key] = content_links
            else:
                print('--jump:%s'%(i_key))
                continue
            #break
        #break
    with open(o_json_name, 'w') as outfile:
        json.dump(article_link_map, outfile)
if __name__ == "__main__":
    download_map_file = 'data/download_map.json'
    article_link_map_file = 'data/article_link_map.json'

    # download_map2json(download_map_file)

    countinue_main = '儿科学'
    countinue_inside = '小儿感冒'
    get_article_from_download_map(download_map_file, article_link_map_file, countinue_main, countinue_inside)
