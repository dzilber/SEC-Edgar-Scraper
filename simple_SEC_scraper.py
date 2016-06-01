from bs4 import BeautifulSoup
import requests
import re
import xml.etree.ElementTree as ET
import urllib
import pandas as pd

# sample: apple 10-q forms

def get_10Q(CIK, filing_type = '10-q', records = 10):
    # sample_search_link = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-q&dateb=&owner=exclude&count=40'
    search_url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK='+CIK+'&type='+filing_type+'&dateb=&owner=exclude&count=40'
    search_webpage = requests.get(search_url)
    search_html_data = search_webpage.text

    # This soup has links to document pages. (Tier 1)
    # The document pages have links to data.  (Tier 2)
    soups = BeautifulSoup(search_html_data, "html.parser")
    attributes = soups.find_all('a')
    links = [i.get('href') for i in attributes]
    tier1_links = [l for l in links if 'Archive' in l] # not sure about this

    # within tier 1 document page, need to find XML docs
    base = 'https://www.sec.gov'
    files_created = []
    for doc_link in tier1_links[:records]:

        document_page = base + doc_link
        webpage = requests.get(document_page)
        html_data = webpage.text
        soup2 = BeautifulSoup(html_data, "html.parser")
        # find attributes again, take href
        a_tagged_html = soup2.find_all('a')
        hrefs = [i.get('href') for i in a_tagged_html]
        # filter for #.xml ending
        xml_links = [i for i in hrefs if re.search("[0-9][.]xml", i)]

        # expect single match
        if len(xml_links)==1:
            filename = xml_links[0].split('/')[-1]
            f = open(filename,'w')
            final_xml = base + xml_links[0]
            data_doc = requests.get(final_xml)
            f.write(data_doc.text)
            f.close()
            files_created.append(filename)
        else:
            print(xml_links)

    return files_created


def get_numbers_from_xml(xml_file):
    # tree = ET.parse('aapl-20151226.xml')
    tree = ET.parse(xml_file)
    root = tree.getroot()
    dicto = {}
    for child in root:
        # print(root.get(child))
        item = child.tag.split('}')[1]
        val = child.text
        if val is None:
            continue
        if any( [i in item for i in ['unit', 'context', 'TextBlock']]):
            continue
        # print (item, val)
        dicto[item]=val
    dicto['Source'] = xml_file

    return pd.Series(dicto)



if __name__ == "__main__":
    CIK = '0000320193' # aapl
    # files_created = get_10Q(CIK)
    # print(files_created)
    files_created = ['aapl-20160326.xml', 'aapl-20151226.xml', 'aapl-20150627.xml', 'aapl-20150328.xml', 'aapl-20141227.xml', 'aapl-20140628.xml', 'aapl-20140329.xml', 'aapl-20131228.xml', 'aapl-20130629.xml', 'aapl-20130330.xml']
    
    paired_results = pd.DataFrame([get_numbers_from_xml(filename) for filename in files_created])

    
    print(paired_results)
    paired_results.to_csv('Apple_consolidated.csv')

