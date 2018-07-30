import json
import requests
import re
import time
import math
import os
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
        'language': 'cn'
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

target_file = './data/article_combine_result.txt'
tokenize_folder = './data/tokenize_haodf/article_tokenize'
model_file = './data/w2v_haodf.bin'
cut_num = 300
def tokenize_flow():
    global target_file
    global tokenize_folder
    global cut_num
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
    
    start_i = 0
    start_t = time.time()
    pool = mp.Pool(processes=2)
    for cut_i in range(cut_num):
        end_i = math.ceil(len(contents)*(cut_i+1)/cut_num)
        sentences = contents[start_i:end_i]
        out_file_name = tokenize_folder+'_'+str(cut_i)+'.json'

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

def tokenize_files_w2v_flow():
    global tokenize_folder
    global cut_num
    model = None

    with open('./data/stopword_cn.txt') as fp:
        stop_words = fp.readlines()
    stop_words = [ stop_word.replace('\n', '') for stop_word in stop_words ]
    all_file_result = [] 
    for load_i in range(cut_num):
        out_file_name = tokenize_folder+'_'+str(load_i)+'.json'
        if(not os.path.exists(out_file_name)):
            print('no %s' % (out_file_name))
            continue
        file_result = {}
        with open(out_file_name, 'r') as outfile:
            file_result = json.load(outfile)
        # results = [x for x in file_result if not x is None]
        # # for row_i in range(len(file_result)):
        # #     file_row = file_result[row_i]
        # #     if file_row is None:
        # #         print("%d, %d is None" % (load_i, row_i))
        # # print(len(file_result))
        # results = [
        #     [ token 
        #     for token in tokens 
        #     if token not in stop_words
        #     ]
        #     for tokens in results
        # ]
        results = []
        for row_i in range(len(file_result)):
            tokens = file_result[row_i]
            if not tokens is None:
                token_ns = []
                for token in tokens:
                    if token not in stop_words:
                        token_ns.append(token)
                if(len(token_ns) !=0 ):
                    all_file_result.append(token_ns)
                    # results.append(token_ns)
                # model = continue_train_w2v(results, model)
            else:
                print("%d, %d is None" % (load_i, row_i))
    model = continue_train_w2v(all_file_result, model)
    print('write %s' % (model_file))
    model.save(model_file)

def continue_train_w2v(new_data, model):
    if not model is None:
        # new_data: more sentences
        # total_examples: number of additional sentence
        # epochs: provide your current epochs. model.epochs is ok 
        print('update model')
        print(model.train(new_data, total_examples=len(new_data), epochs=model.epochs))
        return model
    else:
        print('create model')
        return Word2Vec(new_data, size=400, window=5, min_count=5, workers=4)

if __name__ == "__main__":
    # tokenize_flow()
    tokenize_files_w2v_flow()

    # w2v_tmp_model = Word2Vec.load('./data/w2v_haodf_tmp.bin')
    # w2v_model = Word2Vec.load('./data/w2v_haodf.bin')
    # test_word = w2v_tmp_model.wv.index2word[10]
    # print(test_word)
    # print(w2v_tmp_model.wv.most_similar([test_word], topn=10))
    # print(w2v_model.wv.most_similar([test_word], topn=10))