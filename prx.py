#!/usr/bin/python3

import urllib3
import requests
import threading
import sys, os
import numpy as np
import time
import schedule
import argparse
from bs4 import BeautifulSoup

PROXY_SCRAPE_URL = "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=3000&country=all&ssl=yes&anonymity=all"
PROXY11_URL = 'https://proxy11.com/api/proxy.txt?key=MTY0Nw.XzBqIQ.vQKDGJbd_AtxtSb2O-S8DFAkX2g'
FREE_PROXY_LIST_URL = 'https://free-proxy-list.net/'
TEST_URL = "http://google.com"
TIMEOUT = 3
bad_proxy_count = 0
good_proxy_count = 0

class ProxyChecker(threading.Thread):
    def __init__(self, proxies, good_file):
        threading.Thread.__init__(self)
        self.proxies = proxies
        self.good_file = good_file
    
    def check(self, proxy):
        # 
        # https://github.com/pythonism/proxy-checker/blob/master/prox.py
        # 
        '''
            Function for check proxy return ERROR
            if proxy is Bad else
            Function return None
        '''
        try:
            session = requests.Session()
            session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
            session.max_redirects = 5
            proxy = proxy.split('\n', 1)[0]
            print('Checking ' + proxy)
            session.get(TEST_URL, proxies={'http':'http://' + proxy}, timeout=TIMEOUT, allow_redirects=True)
        except Exception as e:
            # print('Error!')
            return e

    def run(self):
        for proxy in self.proxies:
            global bad_proxy_count
            global good_proxy_count
            if self.check(proxy):
                print('Bad proxy ' + proxy)
                threadLock.acquire()
                bad_proxy_count = bad_proxy_count+1
                threadLock.release()
            else:
                print('Good proxy ' + proxy)
                threadLock.acquire()
                self.good_file.write(proxy)
                good_proxy_count = good_proxy_count+1
                threadLock.release()

def scrape_proxyscrape():
    r = requests.get(PROXY_SCRAPE_URL, allow_redirects=True)
    open("proxy.txt", "wb").write(r.content)
    print("Done scrape: proxyscrape!!")

def scrape_proxy11():
    r = requests.get(PROXY11_URL, allow_redirects=True)
    open("proxy.txt", "ab").write(r.content + str.encode("\n"))
    print("Done scrape: proxy11!!")

def scrape_free_proxy_list():
    r = requests.get(FREE_PROXY_LIST_URL, allow_redirects=True)
    soup = BeautifulSoup(r.text, "lxml")
    with open("proxy.txt", "a") as proxy_file:
        # 
        # https://stackoverflow.com/a/48431336
        # 
        for items in soup.select("#proxylisttable tbody tr"):
            proxy = ':'.join([item.text for item in items.select("td")[:2]])
            proxy_file.write(proxy + "\n")
    print("Done scrape: free_proxy_list!!")

threadLock = threading.Lock()

def remove_duplicate():
    proxy_file = open("proxy.txt")
    list_proxy = list(proxy_file)
    len1 = len(list_proxy)
    list_proxy = list(dict.fromkeys(list_proxy))
    len2 = len(list_proxy)
    proxy_file.close()
    proxy_file = open("proxy.txt", "w")
    for proxy in list_proxy:
        proxy_file.write(proxy)
    proxy_file.close()
    print("Removed %d duplicate proxies" % (len1 - len2))

def check_proxy():
    try:
        proxy_file = open("proxy.txt")
        proxies = list(proxy_file)
        proxy_file.close()
    except Exception:
        sys.exit()

    splited_proxies = np.array_split(proxies, number_of_thread)

    good_file = open("proxy.txt", "w")
    threads = []
    for i in range(0, number_of_thread):
        threads.append(ProxyChecker(splited_proxies[i], good_file))
        threads[i].start()

    for t in threads:
        t.join()

    good_file.close()
    write_real_good_file()
    print("Done!!")
    print("Good proxy: %d/%d" % (good_proxy_count, good_proxy_count+bad_proxy_count))

def grab_and_check():
    scrape_proxyscrape()
    scrape_proxy11()
    scrape_free_proxy_list()
    remove_duplicate()
    check_proxy()

def write_real_good_file():
    temp_good_file = open("proxy.txt")
    good_file = open("good.txt", "w")
    good_file.write(temp_good_file.read())
    temp_good_file.close()
    good_file.close()

def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def enablePrint():
    sys.stdout = sys.__stdout__

if __name__ == "__main__":
    number_of_thread = 10
    interval = 1

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--silent", help="don't print anything", action="store_true")
    parser.add_argument("-t", "--thread", help="number of threads")
    parser.add_argument("-i", "--interval", help="interval between two execution")

    args = parser.parse_args()
    if args.silent:
        blockPrint()
    if args.thread:
        number_of_thread = int(args.thread)
    if args.interval:
        interval = int(args.interval)

    print("Thread:      %d" % number_of_thread)
    print("Interval:    %d" % interval)

    schedule.every(interval).minutes.do(grab_and_check)
    while True:
        schedule.run_pending()
        time.sleep(1)
