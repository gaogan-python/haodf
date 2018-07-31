# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import json
import glob
import os


def QA_crawl(url):
    for retry_i in range(3):
        try:
            content = []
            print(url)
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')

            if res.status_code != 200:
                print('--- WARNING! STATUS CODE NOT 200 ---')
                print('retry %d' %(retry_i))
                continue
            
            tag_name = 'div.content div.question-dialog-list div.question-dialog-content'
            articles = soup.select(tag_name)
            for item in articles:
                content.append(item.text)
            time.sleep(0.5) # each request sleep 0.5 sec
            return content
        except Exception as e: print(e)
        time.sleep(3) # fail retry after sleep 3 sec
    return False

def main():
    # load 所有爬到的網站
    path = './QA/'
    store_path = os.path.abspath(os.path.dirname(__file__))+'/data_download/'
    print(path)
    branches = [branch for branch in glob.glob(path + 'QA*.json')]
    for branche in branches:
        print(branche)
    branch_index = 11
    while(branch_index < len(branches)):
        with open(branches[branch_index],"r") as f:
            start_time = time.time()
            QA_content = []
            print('branch_index:%d' % (branch_index))
            print('branch name:%s' % (branches[branch_index][5:-5]))
            data = json.load(f)
            print('total QA:', len(data), end='\n')
            
            start = 0
            for u in data[start:]:
                print('crawling: {0}/{1} QA'.format(data.index(u), len(data)), end='...')
                # print('QA url:', u)
                content = QA_crawl(u)
                if content:
                    QA_content.append([u, content])
                else:
                    with open('fail_url.txt', 'a') as the_file:
                        the_file.write(branches[branch_index]+' fail: '+u+'\n')
                    QA_content.append([u, []])
                print('done', end=' ')
                print('{:.2f}'.format((time.time() - start_time)/60), 'min')
                
                # 每一百就輸出
                cut = 100
                if data.index(u) == len(data)-1:
                    with open(store_path+"QA_content_"+branches[branch_index][5:-5]+'_final'+'.json',"w") as f:
                        json.dump(QA_content, f)
                    # print('all done')
                if (data.index(u)+1) % cut == 0:
                    with open(store_path+"QA_content_"+branches[branch_index][5:-5]+str(data.index(u)-cut+1)+'-'+str(data.index(u))+'.json',"w") as f:
                        json.dump(QA_content, f)
                    print('--- page {0} - {1} done ---'.format(str(data.index(u)-cut+1), str(data.index(u))))
                    QA_content = []
            branch_index = branch_index+1

if __name__ == '__main__':
    main()