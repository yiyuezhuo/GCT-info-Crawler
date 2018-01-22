# -*- coding: utf-8 -*-
"""
Created on Mon Sep 18 08:17:44 2017

@author: yiyuezhuo
"""

import requests
from bs4 import BeautifulSoup
import re
import webbrowser
import os
#import pickle
import json
#import shutil


def fff(res,cache_name='tmp.html'):
    with open(cache_name,'wb') as f:
        f.write(res.content)
    webbrowser.open(cache_name)
    

# sanity check
url = 'http://yz.chsi.com.cn/zsml/pages/getZy.jsp'
url2 = 'http://yz.chsi.com.cn/zsml/querySchAction.do?ssdm=32&dwmc=%E5%8D%97%E4%BA%AC%E7%90%86%E5%B7%A5%E5%A4%A7%E5%AD%A6&mldm=08&mlmc=%E5%B7%A5%E5%AD%A6&yjxkdm=0811&zymc=&pageno=2'
url3 = 'http://yz.chsi.com.cn/zsml/kskm.jsp?id=102882110608110405&dwmc=(10288)%E5%8D%97%E4%BA%AC%E7%90%86%E5%B7%A5%E5%A4%A7%E5%AD%A6&yxsmc=(106)%E8%AE%A1%E7%AE%97%E6%9C%BA%E5%AD%A6%E9%99%A2&zymc=(081104)%E6%A8%A1%E5%BC%8F%E8%AF%86%E5%88%AB%E4%B8%8E%E6%99%BA%E8%83%BD%E7%B3%BB%E7%BB%9F&yjfxmc=(05)%28%E5%85%A8%E6%97%A5%E5%88%B6%29%E5%9B%BE%E5%BD%A2%E5%9B%BE%E5%83%8F%E6%8A%80%E6%9C%AF%E4%B8%8E%E5%BA%94%E7%94%A8'


data = {
    'mldm':'07' # 直接get不使用post可以获取全部。dmmc的list.另外07理学，08工学
}

host='http://yz.chsi.com.cn'
res = requests.post(url,data = data)
res2 = requests.get(url2)
res3 = requests.get(url3)

dmmc_list = res.json() # dm:序号，mc：学科类别 如0101 哲学 0811 控制科学与工程

def get_now_total(soup):
    # fuck the page refactor
    now = soup.select_one('li.selected').select_one('a').text
    #total = soup.select_one('.ch-page').select('li')[-2].select_one('a').text
    #text_list = [li.select_one('a').text for li in soup.select_one('.ch-page').select('li')]
    #total = [text for text in text_list if text.isdigit()][-1]
    text_list = []
    for li in soup.select_one('.ch-page').select('li'):
        if li.select_one('a'):
            text = li.select_one('a').text
            if text.isdigit():
                text_list.append(text)
    total = text_list[-1]
    return now,total
        
    
def dmmc_pageno_info_post(dmmc,pageno):
    url = 'http://yz.chsi.com.cn/zsml/queryAction.do'
    data = {'ssdm':'',
            'dwmc':'',
            'mldm':dmmc['dm'][:2], # '08'
            'mlmc':dmmc['mc'], # ‘工学’
            'yjxkdm':dmmc['dm'], # '0811'
            'zymc':'',
            'pageno':pageno, # '1'
    }
    res  = requests.post(url, data)
    return res

def dmmc_pageno_info(dmmc,pageno):
    assert isinstance(pageno,str)
    info = {'url_list':[],'name_list':[],'total':None,'now':None}
    '''
    url = 'http://yz.chsi.com.cn/zsml/queryAction.do'
    data = {'ssdm':'',
            'dwmc':'',
            'mldm':dmmc['dm'][:2], # '08'
            'mlmc':dmmc['mc'], # ‘工学’
            'yjxkdm':dmmc['dm'], # '0811'
            'zymc':'',
            'pageno':pageno, # '1'
    }
    res  = requests.post(url, data)
    '''
    res = dmmc_pageno_info_post(dmmc,pageno)
    soup = BeautifulSoup(res.content,"lxml")
    table = soup.select('table')[-1]
    for tr in table.select('tr'):
        a = tr.select('a')
        if len(a) == 0:
            continue
        href = a[0].attrs['href']
        info['name_list'].append(a[0].text)
        info['url_list'].append(host + href.replace('amp;',''))
    #now,total = soup.select('#page_total')[0].text.split('/')
    now,total = get_now_total(soup)
    info['now'] = int(now)
    info['total'] = int(total)
    return info
    
def major_examination_info(major_examination_url):
    #print(major_examination_url)
    res = requests.get(major_examination_url)
    soup = BeautifulSoup(res.content,'lxml')
    method_l = []
    for tbody in soup.select('.zsml-res-items'):
        tbody_content = []
        for td in tbody.select('td'):
            '''
            <td>
                            (101)思想政治理论
                            <span class="sub-msg">见招生简章</span>
            </td>
            '''
            tbody_content.append(td.next.strip())
        method_l.append(tbody_content)
    return method_l
            
    
def dmmc_to_school(dmmc):
    head = dmmc_pageno_info(dmmc,'1')
    if head['total'] == 1:
        return {'name_list':head['name_list'], 'url_list':head['url_list']}
    name_list = head['name_list'].copy()
    url_list = head['url_list'].copy()
    for i in range(2,head['total']+1):
        info = dmmc_pageno_info(dmmc,str(i))
        assert i == info['now']
        url_list.extend(info['url_list'])
        name_list.extend(info['name_list'])
    return {'name_list':name_list, 'url_list':url_list}

    
def school_info(school_page_url):
    info = {'major_list':[],'total':None,'now':None}
    res = requests.get(school_page_url)
    soup = BeautifulSoup(res.content,'lxml')
    for tr in soup.select('table')[-1].select('tr'):
        al = tr.select('a')
        if len(al) == 0:
            continue
        a = al[0]
        major = {}
        major_examination_url = host + a.attrs['href'].replace('&amp','')
        major['examination'] = major_examination_info(major_examination_url)
        tdl = tr.select('td')
        major['institute'] = tdl[0].text # 学院
        major['code'] = tdl[1].text
        major['direction'] = tdl[2].text
        script_text = str(tr.select('script')[1].text)
        major['number'] = re.findall(r"cutString\('(.*)',6\)",script_text)[0]
        info['major_list'].append(major)
    #now,total = soup.select('#page_total')[0].text.split('/')
    now,total = get_now_total(soup)
    info['now'] = int(now)
    info['total'] = int(total)
    return info

def school_to_recruit_examation(school_url):
    head = school_info(school_url+'&pageno=1')
    if head['total'] == 1:
        return {'major_list':head['major_list']}
    major_list = head['major_list'].copy()
    for i in range(2,head['total']+1):
        school_page_url = school_url + '&pageno=' + str(i)
        info = school_info(school_page_url)
        assert i == info['now']
        major_list.extend(info['major_list'])
    return {'major_list':major_list}

def dmmc_to_major(dmmc,disp=True,retry_limit=10,cache_dir='cache',instant=True):
    schools = dmmc_to_school(dmmc)
    major_list = []
    for school_name,school_url in zip(schools['name_list'],schools['url_list']):
        if disp:
            print('Collecting {}'.format(school_name))
        
        for i in range(retry_limit):
            try:
                if not instant:
                    
                    major_list_part = school_to_recruit_examation(school_url)['major_list']
                    
                else:
                    root = os.path.join(cache_dir,dmmc['dm'])
                    if not os.path.isdir(root):
                        os.makedirs(root)
                    path = os.path.join(root,school_name)
                    
                    if os.path.isfile(path):
                        print('pass {}'.format(school_name))
                    else:
                        
                        major_list_part = school_to_recruit_examation(school_url)['major_list']
                        for major in major_list_part:
                            major['school'] = school_name

                        with open(path, 'w') as f:
                            #pickle.dump(result, f)
                            json.dump(major_list_part, f , ensure_ascii=False, indent=1)
                break
            except requests.exceptions.ConnectionError:
                if disp:
                    print('Connecting fail try {}/{}'.format(i+1,retry_limit))
        else:
            raise ConnectionAbortedError
        if not instant:
            for major in major_list_part:
                major['school'] = school_name
            major_list.extend(major_list_part)
    return major_list
    
def download_dmmc_list(dmmc_list,disp=True,cache_dir='cache',instant=True):
    os.makedirs(cache_dir,exist_ok=True)
    for dmmc in dmmc_list:
        if not instant:
            path = os.path.join(cache_dir,dmmc['dm'])
        
        
        if (not instant) and os.path.isfile(path):
            if disp:
                print('Skip {} {}'.format(dmmc['dm'],dmmc['mc']))
            continue
        
        if disp:
            print('Start Collecting {} {}'.format(dmmc['dm'],dmmc['mc']))
        
        root = os.path.join(cache_dir,dmmc['dm'])
        if instant:
            if not os.path.isdir(root):
                os.makedirs(root)
                with open(os.path.join(root,'.uncompleted'),'w'):
                    pass
                
        if (not instant) or os.path.isfile(os.path.join(root,'.uncompleted')):
            result = dmmc_to_major(dmmc, disp = disp,cache_dir=cache_dir,instant=instant)
        else:
            print('skip {}'.format(dmmc['dm']))
        
        if instant and os.path.isfile(os.path.join(root,'.uncompleted')):
            os.remove(os.path.join(root,'.uncompleted'))
            with open('completed','w'):
                pass
        
        if not instant:
            with open(path, 'w') as f:
                #pickle.dump(result, f)
                json.dump(result, f, ensure_ascii=False, indent=1)
        
    
def download_all(disp=True,cache_dir='cache'):
    dmmc_list = requests.get(url).json()
    download_dmmc_list(dmmc_list,disp=disp,cache_dir=cache_dir)
    
def download_sci_tech(disp=True,cache_dir='cache'):
    dmmc_list = requests.get(url).json()
    dmmc_list = [dmmc for dmmc in dmmc_list if dmmc['dm'][:2] in ['07','08']]
    download_dmmc_list(dmmc_list,disp=disp,cache_dir=cache_dir)

DEBUG = False

if DEBUG:
    dmmc_list = requests.get(url).json()
    dmmc = dmmc_list[0]
    res = dmmc_pageno_info_post(dmmc,'1')
    soup = BeautifulSoup(res.content,"lxml")
    
    now = soup.select_one('li.selected').select_one('a').text
    total = soup.select_one('.ch-page').select('li')[-2].select_one('a').text
