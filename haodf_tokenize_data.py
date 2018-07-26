import json
import requests
import re
import time
import math
from gensim.models import Word2Vec
from multiprocessing import Process
import multiprocessing as mp

def run_p(sentences, cut_i, out_file_name):
    # sentences = arguments_list[0]
    # cut_i = arguments_list[1]
    # out_file_name = arguments_list[2]
    
    ## GO TOKENIZER
    # TOKENIZER_URL = 'http://localhost:8002/tokenize'
    TOKENIZER_URL = 'http://192.168.10.108:8002/tokenize'

    headers = { 'content-type': 'application/json' }

    payload = {
        'sentences': sentences,
        'language': 'tw'
    }
    # print('sentences len: %d' % (len(sentences)))

    start_cut_t = time.time()
    res = requests.post(TOKENIZER_URL, headers=headers, data=json.dumps(payload))
    response = res.json()
    # print(response)

    result_tmp = []
    if 'data' in response:
        result = response['data']
        # print(result)
        if len(result) > 0 :
            result_tmp.extend(result)
    else:
        print(response)
    print('len(result_tmp): %d' % (len(result_tmp)))
    print('cut_%d Tokenize takes %f seconds.' % (cut_i,time.time()-start_cut_t))

    with open(out_file_name, 'w') as outfile:
        json.dump(result_tmp, outfile)
    outfile.close()
    print('save file: %s' % (out_file_name))
    return cut_i,time.time()-start_cut_t

def main():
    ### health-articles-2.json
    '''
    target_file = 'health-articles-2.json'
    tokenize_file = 'tokenize_data.json'
    with open(target_file) as fp:
        text = fp.read()

    jsonfile = json.loads(text)
    articles = jsonfile['articles']
    #print(articles[-1])

    contents = [article['content'] for article in articles ]
    #print(contents[0])

    filtering = re.compile('[a-zA-Z0-9.:?]')
    #print (" ".join([str(len(content)) for content in contents[-10:-1]]))
    contents = [ filtering.sub('', content) for content in contents ]
    #print (" ".join([str(len(content)) for content in contents[-10:-1]]))
    '''
    ### wiki_zh_tw.txt
    target_file = './data/article_combine_result.txt'
    tokenize_file = './tokenize_haodf/article_tokenize'
    contents = []
    filtering = re.compile('[a-zA-Z0-9.:?]')
    with open(target_file,'r') as f:
        for line in f:
            line = line.strip() # remove space in head and tail
            line = filtering.sub('', line) # remove english and number
            contents.append(line) # split and sppend to contents
    f.close()
    print('contents length:',len(contents))
    print('contents[0] length:',len(contents[0]))
    ###
    # request once, this will be more faster than below.(tokenize service has parallelization)

    # contents = contents[-10:]
    
    cut_num = 300
    start_i = 0
    start_t = time.time()
    pool = mp.Pool(processes=2)
    for cut_i in range(cut_num):
        end_i = math.ceil(len(contents)*(cut_i+1)/cut_num)
        sentences = contents[start_i:end_i]
        out_file_name = tokenize_file+'_'+str(cut_i)+'.json'

        # run_p(sentences, cut_i, out_file_name)
        # arguments_list = [sentences, cut_i, out_file_name]

        # res = pool.apply_async(run_p, args=(sentences, cut_i, out_file_name))
        res = run_p(sentences, cut_i, out_file_name)
        print('apply_async request %d , start_i %d, end_i %d' % (cut_i, start_i, end_i))
        start_i = end_i
        if cut_i == 5:
            break
    pool.close()
    pool.join()
    print('total Tokenize takes %f seconds.' % (time.time()-start_t))
    ###
    # request by each article, don't use this.(it will be slower than request once)
    '''
    now_i = 0
    total_start_t = time.time()
    for content in contents:
        payload = {
        'sentences': [content],
        'language': 'tw'
        }

        #print(content)
        start_t = time.time()
        res = requests.post(TOKENIZER_URL, headers=headers, data=json.dumps(payload))
        #print(res.json())
        response = res.json()
        if 'data' in response:
            result = response['data']
            if len(result) > 0 :
                results.extend(result)
        now_i = now_i+1
        print('request : '+str(now_i)+'/'+str(len(contents)))
        print('Tokenize takes '+ str(time.time()-start_t)+' seconds.')
    print('Tokenize total takes '+ str(time.time()-total_start_t)+' seconds.')
    '''
    ###

    # print('result, contents : ',len(results), ', ', len(contents))

    # outfile = [ ' '.join(result) for result in results ]
    # with open('tokenize_data.txt', 'w') as fp:
    #     fp.write('\n'.join(outfile))
    '''
    with open(tokenize_file, 'w') as outfile:
        json.dump(results, outfile)
    outfile.close()
    print('save file: %s' % (tokenize_file))
    '''
if __name__ == "__main__":
    main()