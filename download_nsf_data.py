# Code to download archived NSF data (XML files) from the web
#
# Mark Saddler
#

import os
import requests
import bs4
import urllib
import re
import zipfile


def get_soup_from_url(url):
    request = requests.get(url)
    html = request.text.encode('iso-8859-1')
    return bs4.BeautifulSoup(html, "lxml")


def get_data_links(soup, url):
    data_links = []
    path_url = url.strip('download.jsp')
    data_tag_list = soup.find_all('div', class_ = 'downloadcontent')
    for data_tag in data_tag_list:
        link_tag_list = data_tag.find_all('a', {'href' : True})
        for link_tag in link_tag_list:
            link = link_tag['href']
            data_links.append(path_url + link)
    return data_links


def download_zipfile(url, zip_file_path):
    pattern = r'DownloadFileName=\w*'
    match = re.search(pattern,url)
    if match:
        dl_fn = match.group().strip('DownloadFileName=')
        dl_fn = zip_file_path + dl_fn
        return urllib.request.urlretrieve(url, dl_fn)
    else:
        print('Incompatible download link')
        return None
    # Returns tuple: (dl_fn, headers)


def extract_zipfile(zipped_directory, output_directory):
    z = zipfile.ZipFile(zipped_directory, 'r')
    z.extractall(output_directory)
    z.close()
    os.remove(zipped_directory)



url = 'https://www.nsf.gov/awardsearch/download.jsp'
soup = get_soup_from_url(url)
link_list = get_data_links(soup, url)

zip_file_path = '/home/student/cs122_MVR/data/nsf/temp'

for tmp_link in link_list[0:5]: # <-------------------- Download 5 most recent years
    print('Downloading: ' + tmp_link)
    (zip_file, headers) = download_zipfile(tmp_link, zip_file_path)
    print('Extracting zipfile: ' + zip_file)
    data_file = zip_file.replace('temp', '')
    extract_zipfile(zip_file, data_file)