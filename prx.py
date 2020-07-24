import urllib3
import requests
import threading
import sys, os
import numpy as np
import time
import schedule
import argparse

PROXY_SCRAPE_URL = "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=3000&country=all&ssl=yes&anonymity=all"
TEST_URL = "http://google.com"
TIMEOUT = 3

class ProxyChecker(threading.Thread):
    def __init__(self, proxies, good_file):
        threading.Thread.__init__(self)
        self.proxies = proxies
        self.good_file = good_file
    
    def check(self, proxy):
        '''
            Function for check proxy return ERROR
            if proxy is Bad else
            Function return None
        '''
        try:
            session = requests.Session()
            session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
            session.max_redirects = 5
            proxy = proxy.split('\n',1)[0]
            print('Checking ' + proxy)
            session.get(TEST_URL, proxies={'http':'http://' + proxy}, timeout=TIMEOUT, allow_redirects=True)
        except Exception as e:
            # print('Error!')
            return e

    def run(self):
        for proxy in self.proxies:
            if self.check(proxy):
                print('Bad proxy ' + proxy)
            else:
                print('Good proxy ' + proxy)
                threadLock.acquire()
                self.good_file.write(proxy)
                threadLock.release()

def scrape_proxy():
    r = requests.get(PROXY_SCRAPE_URL, allow_redirects=True)
    open("proxy.txt", "wb").write(r.content)
    print("Done scrape!!")

threadLock = threading.Lock()

def check_proxy():
    good_file = open("temp_good.txt", "w")

    try:
        proxy_file = open("proxy.txt")
        proxies = list(proxy_file)
        proxy_file.close()
    except Exception:
        sys.exit()

    splited_proxies = np.array_split(proxies, number_of_thread)

    threads = []
    for i in range(0, number_of_thread):
        threads.append(ProxyChecker(splited_proxies[i], good_file))
        threads[i].start()

    for t in threads:
        t.join()

    good_file.close()
    write_real_good_file()
    print("Done!!")

def grab_and_check():
    scrape_proxy()
    check_proxy()

def write_real_good_file():
    temp_good_file = open("temp_good.txt")
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
    interval = 10

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

    schedule.every(interval).minutes.do(grab_and_check)
    while True:
        schedule.run_pending()
        time.sleep(1)
