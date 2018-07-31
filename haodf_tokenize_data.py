# -*- coding: utf-8 -*-
import json
import requests
import re
import time
import math
import os
from gensim.models import Word2Vec
from multiprocessing import Process
import multiprocessing as mp

def cut_too_long(sentence ,long_target):
    cut_ind = 0
    sentence = sentence.strip()
    remaining_sentance = sentence[cut_ind:]
    short_sentence_list = []
    # print('long_target = %d' % (long_target))
    while (True):
        search_ind = cut_ind+long_target
        search_sentance = sentence[search_ind:]
        space_ind = search_sentance.find(" ")
        if(space_ind != -1):
            short_sentence_list.append(sentence[cut_ind:search_ind+space_ind])
            cut_ind = search_ind+space_ind+1
            remaining_sentance = sentence[cut_ind:]
        else:
            short_sentence_list.append(sentence[cut_ind:])
            cut_ind = len(sentence)
            remaining_sentance = []
            break
    return short_sentence_list

def run_p(sentences, cut_i, out_file_name):
    # sentences = arguments_list[0]
    # cut_i = arguments_list[1]
    # out_file_name = arguments_list[2]

    ## GO TOKENIZER
    # TOKENIZER_URL = 'http://localhost:8002/tokenize'
    TOKENIZER_URL = 'http://192.168.10.108:8002/tokenize'

    headers = { 'content-type': 'application/json' }

    long_target = 500
    short_sentences = []
    for sentence in sentences:
        short_results = cut_too_long(sentence, long_target)
        short_sentences.extend(short_results)
    print('len(short_sentences):%d' % (len(short_sentences)))
    # print(short_sentences[0])
    # print(short_sentences[-1])
    result_tmp = []
    start_cut_t = time.time()

    payload = {
        'sentences': short_sentences,
        'language': 'cn'
    }
    # print('sentences len: %d' % (len(sentences)))

    res = requests.post(TOKENIZER_URL, headers=headers, data=json.dumps(payload))
    response = res.json()
    # print(response)

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
cut_num = 1200
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
    start_file_num = 18
    for cut_i in range(cut_num):
        end_i = math.ceil(len(contents)*(cut_i+1)/cut_num)
        if cut_i < start_file_num:
            start_i = end_i
            print('--jump cut_%d' %(cut_i))
            continue
        print('start cut_%d' % (cut_i))
        sentences = contents[start_i:end_i]
        out_file_name = tokenize_folder+'_'+str(cut_i)+'.json'

        # run_p(sentences, cut_i, out_file_name)
        # arguments_list = [sentences, cut_i, out_file_name]

        # res = pool.apply_async(run_p, args=(sentences, cut_i, out_file_name))

        print('apply_async request %d , start_i %d, end_i %d' % (cut_i, start_i, end_i))
        res = run_p(sentences, cut_i, out_file_name)
        start_i = end_i
        # if cut_i == 20:
        #     break
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
    total_i = 0
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
                # print("%d, %d is None" % (load_i, row_i))
                print("index %d is None" %(total_i+row_i+1))
        total_i = total_i + len(file_result)
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
    tokenize_flow()
    # tokenize_files_w2v_flow()

    # w2v_tmp_model = Word2Vec.load('./data/w2v_haodf_tmp.bin')
    # w2v_model = Word2Vec.load('./data/w2v_haodf.bin')
    # test_word = w2v_tmp_model.wv.index2word[10]
    # print(test_word)
    # print(w2v_tmp_model.wv.most_similar([test_word], topn=10))
    # print(w2v_model.wv.most_similar([test_word], topn=10))

    # target_str = '先天性心脏病的如何早期发现 当孩子出现阵发性青紫 气促 吸奶中断时家长才想到要抱到医院来就诊 我接诊了一个 天的新生儿 出生为第一胎 出生时顺产 出生体重有 生长发育的不错 可是生后第二天开始 发现孩子偶出现口周发紫 但家长并没有引起重视 当病情进一步的出现变化了才引起了家长的重视 星期天上午在我查房的同时 就有一位病人家长抱着才几天的孩子 要求就诊 当问清病史后体温发现孩子口周仍有发绀 胸骨左缘 肋间可闻及全收缩期杂音 我考虑是先天性心脏病 室间隔缺损 家长一听 当时就泪水不停的流 为了明确诊断 做心脏彩色多谱勒证实了先天性心脏病 室间隔缺损的诊断 赣南医学院第一附属医院儿科刘跃梅孩子为何会引起先天性心脏病 家长向我一连串的提出了好几个关于先天性心脏病的有关问题 其实 先天性心脏病是一种较为常见的儿童心脏疾病 在我国新生婴儿先天性心脏病的发病率并不低 据专家统计 先天性心脏病的发病率在我国占 左右 大多数的先天性心脏病儿 若能早期发现 均能得到及早的治疗 根据病情合理的选择手术时机及时手术有望彻底的痊愈 并不会影响孩子的正常学习和生长发育 若不能及时的发现就有可能延误治疗 造成一些并发症而导致死亡 先天性心脏病虽说是一种先天性发育畸形但它并不像肢体畸形那样易于早期诊断 若不留心观察 不易发现 若是能早期的发现一些症状 就能早期得到治疗 以免发现意外 因此 当发现小儿有不明原因的烦躁不安 哭声低 吸奶时无力 呼吸急促 哭闹后气喘口周发绀 较大的孩子会说胸闷 心前区不舒服 特别是在活动后上述症状可加重 长时间出现这些症状就会加重体内的缺氧 反复的出现肺部感染 影响身体的正常发育 出现紫绀 最常见的先天性心脏病分为二型 无青紫型 青紫型 应根据孩子的病情变化及辅助检查确诊无青紫型先天性心脏病多见于房间隔缺损和室间隔缺损 青紫型先天性心脏病多见于法洛氏四联症 法洛氏四联症的病人常有几种特殊的姿势 婴幼儿期家长抱时不顾伸直双腿 坐时喜欢将脚放在凳子上 站着时下肢保持弯曲的姿势 年龄行走时易出现蹲距现象 因为活动后下蹲一会可增加体循环阻力增加肺活量 有利于减轻心脏的负担 改善缺氧状况 由于先天性心脏病的病人如房间隔缺损 室间隔缺损的病人 由于肺血多 容易反复的出现呼吸道的感染及肺炎 生长发育明显的迟缓 因为肺循环血量增加后导致体循环血量下降 使孩子生长发育受到影响 通常情况下 患有严重先天性心脏病的小儿 应早期明确诊断 必须到医院做全面的体格检查 摄心脏三位片心电图 心脏彩色多谱勒等 必要的还必须行心导管的检查 对这种病人一般情况下选择的手术的时机多在 岁更为合适 若病情重 变化快的病人 就应根据病人的病情 适时的进行手术治疗 以达到彻底的治愈 本文系刘跃梅医生授权好大夫在线 发布 未经授权请勿转载'
    # long_target = 500
    # result = cut_too_long(target_str, long_target)
    # print(len(target_str))
    # print(target_str)
    # print('-----')
    # add_tmp = 0
    # for raw in result:
    #     add_tmp = add_tmp + len(raw)
    #     print(len(raw))
    #     print(raw)
    # print('-----')
    # print(add_tmp)
