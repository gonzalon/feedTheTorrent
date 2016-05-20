#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Gonzalo Naveira - @gonzalon

from bs4 import BeautifulSoup
import os
import re
import requests
import subprocess
import sys
import tabulate
import http
import ftplib
 
 
class OutColors:
    DEFAULT = '\033[0m'
    BW = '\033[1m'
    LG = '\033[0m\033[32m'
    LR = '\033[0m\033[31m'
    SEEDER = '\033[1m\033[32m'
    LEECHER = '\033[1m\033[31m'

def load_ignored():
    lines = []
    with open('ignored.csv', 'r') as f:
        for line in f:
            commas = line.split(',')
            for index, c in enumerate(commas):
                lines.append(c)
    return lines

def add_to_ignore_list(new_ignored):
    with open('ignored.csv','a') as f:
            f.write(','+new_ignored )

def find_element_in_list(element, list_element):
    try:
        index_element = list_element.index(element)
        return False
    except ValueError:
        return True

def select_torrent():
    torrent = input('>> ')
    return torrent

def download_torrent(url):
    fname = os.getcwd() + '/' + url.split('title=')[-1] + '.torrent'
    header = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0',}
    r = requests.get("http:"+url, headers=header)
    try:
        if r.status_code == 200:
            with open(fname, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        print('\n' + OutColors.LR + str(e))
 
    return fname

def ftp_file(filename):
    print('Sending via FTP >> ' + filename)
    ftp = ftplib.FTP("192.168.1.106")
    ftp.login("root", "raspberry")
    ftp.cwd("/media/My Book/dl/watch")
    myfile = open(filename, 'rb')
    ftp.storbinary ('STOR ' + filename, myfile)
    myfile.close()
    
def send_delete_torrent(): 
    for fn in os.listdir('.'):
         if os.path.isfile(fn):
            if "torrent" in fn:
                print (fn)
                ftp_file(fn)
    for fn in os.listdir('.'):
         if os.path.isfile(fn):
            if "torrent" in fn:
                os.remove(fn)
    
def manage_user_input(query, href):
    user_input = input('>> ')
    if user_input == 'Q' or user_input == 'q':
        send_delete_torrent()
        sys.exit(0)
    elif user_input == 'S' or user_input == 's':
        user_search = input('>> ')
        aksearch(user_search)
    elif user_input == 'I' or user_input == 'i':
        add_to_ignore_list(query)
    else:
        if int(user_input) <= 0 or int(user_input) > len(href):
            print('Use eyeglasses...')
        else:
            print('Download >> ' + href[int(user_input)-1].split('title=')[-1] + '.torrent')
            fname = download_torrent(href[int(user_input)-1])
            add_to_ignore_list(query)

def menu():
    print(OutColors.DEFAULT+'--------------------------------------------------------------------------------------')
    print(OutColors.DEFAULT+'\nSelect [ i ] to ignore this title or [ s ] to make a manual search or [ q ] to quit')

def aksearch(query):
    tmp_url = 'http://kickass.to/usearch/'
    url = tmp_url + query + '/'
    href = []
    try:
        cont = requests.get(url)
    except requests.exceptions.RequestException as e:
        raise SystemExit('\n' + OutColors.LR + str(e))
 
    # check if no torrents found
    if not re.findall(r'Download torrent file', str(cont.content)):
        print(OutColors.LR+'\nTorrents found: 0.')
        menu()
        manage_user_input(query, href)
    else:
        soup = BeautifulSoup(cont.content, 'html.parser')
        al = [s.get_text() for s in soup.find_all('td', {'class':'center'})]
        href = [a.get('href') for a in soup.find_all('a', {'title':'Download torrent file'})]
        size = [t.get_text() for t in soup.find_all('td', {'class':'nobr'}) ]
        title = [ti.get_text() for ti in soup.find_all('a', {'class':'cellMainLink'})]
        age = al[2::5]
        seeders = al[3::5]
        leechers = al[4::5]
 
        # for table printing
        table = [[OutColors.BW + str(i+1) + OutColors.DEFAULT if (i+1) % 2 == 0 else i+1,
                    OutColors.BW + title[i] + OutColors.DEFAULT if (i+1) % 2 == 0 else title[i],
                    OutColors.BW + size[i] + OutColors.DEFAULT if (i+1) % 2 == 0 else size[i],
                    OutColors.BW + age[i] + OutColors.DEFAULT if (i+1) % 2 == 0 else age[i],
                    OutColors.SEEDER + seeders[i] + OutColors.DEFAULT if (i+1) % 2 == 0 else OutColors.LG + seeders[i] + OutColors.DEFAULT,
                    OutColors.LEECHER + leechers[i] + OutColors.DEFAULT if (i+1) % 2 == 0 else OutColors.LR + leechers[i] + OutColors.DEFAULT] for i in range(len(href))]
        print()
        print(tabulate.tabulate(table, headers=['No', 'Title', 'Size', 'Age', 'Seeders', 'Leechers']))
 
        # torrent selection
        if len(href) == 1:
            torrent = 1
        else:
            menu()
            print(OutColors.DEFAULT+'To select and download a torrent: [ 1 - ' + str(len(href)) + ' ]')
            manage_user_input(query, href)

def imdb_imput():
    print(OutColors.DEFAULT + "\nSearching for the titles in the IMDB list...")
    url = "http://www.imdb.com/user/ur32008707/watchlist"
    req = requests.get(url)
    statusCode = req.status_code
    if statusCode == 200:
        html = BeautifulSoup(req.text, 'html.parser')
        items = html.find_all('h3',{'class':'lister-item-header'})

        for i,item in enumerate(items):
            
            title = item.find('a').getText()
            year = item.find('span', {'class' : 'lister-item-year text-muted unbold'}).getText()
            
            ignored = load_ignored()
            is_not_ignored = find_element_in_list(title, ignored)
            if is_not_ignored:
                print(OutColors.LG + "\nLooking for: "+title + " torrent file.")
                aksearch(title)
    else:
        print("Error!!" , statusCode)
        sys.exit(0)

if __name__ == '__main__':
    try:
        os.system('cls')
        imdb_imput()
    except KeyboardInterrupt:
        os.system('cls')
        print(OutColors.DEFAULT+ "\nSee you! ")