# Helper File
# @Author: Bish Sinha, Data Buddha

import os
import re
import json
import requests
from datetime import datetime
import numpy as np
import pandas as pd
import PyPDF2 as ppd
import tabula
from bs4 import BeautifulSoup
import config


def get_pdf_files():
    html_content = requests.get(config.URL).text
    soup = BeautifulSoup(html_content, "html.parser")

    pdf_links = []
    for a in soup.find_all('a', attrs = {"target": "_blank"}):
        sr = re.search('.*situation-report.*', a['href'])
        if sr:
            pdf_links.append(a['href'])

    clean_links = ['https://www.who.int' + a for a in pdf_links]
    return clean_links


def get_latest_file(pdf_links):

    latest_pdf_link = pdf_links[0]
    latest_file_name = os.path.basename(latest_pdf_link).split('.pdf')[0]

    local_pdf_file_name = os.path.join(r".\data", latest_file_name + '.pdf')
    print(local_pdf_file_name)

    return latest_pdf_link, latest_file_name, local_pdf_file_name

