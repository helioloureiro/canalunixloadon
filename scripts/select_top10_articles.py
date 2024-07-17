#! /usr/bin/env python3

import re
import random
from typing import List
import time
import json
import sys
import logging
import requests

SITE = "https://github.com"
SITE_RAW = "https://raw.githubusercontent.com/helioloureiro/canalunixloadon/master"
SITE_PATH = "/helioloureiro/canalunixloadon/tree/master/pautas"

save_output = False
output_filename = None

Array = List[str]
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s (%(levelname)s): %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

class Hellib:
    "Supporting tools in static way"
    @staticmethod
    def get_http_content(url: str) -> str:
        "Fetch web page or raise an error"
        req = requests.get(url)
        if req.status_code != 200:
            logger.error(f"Wrong status code: {req.status_code}")
            raise Exception(req.text)
        return req

    @staticmethod
    def line_match(line: str) -> bool:
        "Check whether a line matches pattern or not"
        if not re.search("span", line):
            return False
        if not re.search(r"\.md", line):
            return False
        if not re.search(r"[0-9]\.md", line):
            return False
        return True

    @staticmethod
    def get_latest_file(url: str) -> str:
        article_files = []
        logger.info(f'Fetching from: {url}')
        content = Hellib.get_http_content(url)
    
        ## format changed on github
        ## curl -s https://github.com/helioloureiro/canalunixloadon/tree/master/pautas | grep "react-app.embeddedData" | sed "s/<\/.*//;s/.*>//"
    
        json_body = None
        for line in content.text.splitlines():
            if not re.search("react-app.embeddedData", line):
                continue
            line = re.sub(r"</.*", "", line)
            line = re.sub(r".*>", "", line)
            json_body = json.loads(line)
    
        if json_body is None:
            logger.error("Failed to get json body:", content.text[0:100])
            raise Exception("Failed to get json body")
    
        logger.debug(" = Articles =")
        for link in json_body['payload']['tree']['items']:
            if not re.search(r"\d+", link['name']):
                continue
            logger.debug(" *", link['path'])
            article_files.append(link['path'])
    
        latest = sorted(article_files)[-1]
        logger.info(f"Latest: {latest}")

        return latest



class AgendaBuilder:
    def __init__(self):
        ## docs structure
        self.articles = {
            "Assuntos": [],
            "Sugestões via google forms": [],
            "Sugestões via telegram": [],
            "Que pode ir parar no próximo programa se não der tempo": [],
            "Pra fechar": []
        }

    def run(self):
        "Find latest article and populate self.articles accordingly"
        latest_articles_file = Hellib.get_latest_file(SITE + SITE_PATH)
        agenda_file_url = SITE_RAW + "/" + latest_articles_file
        logger.info(f"Latest agenda url: {agenda_file_url}")
        self.read_articles_file_and_generate_content_dict(agenda_file_url)
        self.print_result()
        self.dump_to_file()


    def read_articles_file_and_generate_content_dict(self, url: str) -> dict:
        """
        It reads the url file as raw text and filter per section to
        create the dictionary.
        """

        body = Hellib.get_http_content(url)
        self.filter_content_per_section(body.text)
        self.get_random_articles(15)

    def filter_content_per_section(self, body: str):
        "Filter content per 2 \n and populate the self.articles dictionary"

        ## removed all 3 \n
        ##body = re.sub(r"\n\n",  "\n\n", body)

        for block in body.split("\n\n"):
            if len(block) < 2 or not re.search(r"\w+", block):
                logger.warning(f"empty block: {block}")
                continue
            title = None
            lines = block.splitlines()

            if len(lines) < 3:
                continue

            ## check whether 2nd line is "=====" or skip it
            if re.search("====================", lines[1]):
                logger.warning("Found ====== pattern on 2nd line")
                title = lines[0]
            ## check whether it is located on 3rd line 
            elif re.search("====================", lines[2]):
                logger.warning("Found ====== pattern on 3 line")
                title = lines[1]
            else:
                logger.warning(f"No pattern found: {block}")

            logger.info(f"Title: {title}")

            if title is None:
                continue
       
            articles = self.get_articles(block)
            logger.info(f"Analyzing: {title}")
            if re.search("Assuntos | link | comentários", title):
                self.articles["Assuntos"] = articles
            elif re.search("Sugestões via google forms", title):
                self.articles["Sugestões via google forms"] = articles 
            elif re.search("Sugestões via telegram", title):
                self.articles["Sugestões via telegram"] = articles
            elif re.search("Que pode ir parar no próximo programa se não der tempo", title):
                self.articles["Que pode ir parar no próximo programa se não der tempo"] = articles
            elif re.search("Pra fechar", title):
                self.articles["Pra fechar"] = articles
            else:
                logger.error(f"Unknown title: {title}")
                raise Exception(f"Unknown title: {title}")

    def render_agenda(self) -> str:
        text = 'Assuntos | link | comentários\n' + \
            '=============================\n' 
        text += "\n".join(self.articles["Assuntos"])

        text += '\n\nSugestões via google forms\n' + \
            '==========================\n'
        text += "\n".join(self.articles["Sugestões via google forms"])

        text += '\n\nSugestões via telegram\n' + \
            '======================'
        text += "\n".join(self.articles["Sugestões via telegram"])

        text += '\n\nQue pode ir parar no próximo programa se não der tempo\n' + \
            '=======================================================\n'
        text += "\n".join(self.articles["Que pode ir parar no próximo programa se não der tempo"])

        text += '\n\nPra fechar\n' + \
        '==========\n'
        text += "\n".join(self.articles["Pra fechar"])

        return text

    def get_articles(self, block: str) -> Array:
        articles = []
        for line in block.splitlines():
            if not re.search(r"\w+", line):
                continue
            if not re.search(r"^\*", line):
                continue
            articles.append(line.rstrip())
        return articles

    def get_random_articles(self, nr_articles: int):
        articles = []
        while (nr_articles > 0):
            nr_articles -= 1
            lottery = random.randint(0, len(self.articles["Que pode ir parar no próximo programa se não der tempo"]) - 1)
            articles.append(
                self.articles["Que pode ir parar no próximo programa se não der tempo"].pop(lottery)
            )

        self.articles["Assuntos"] = articles

    def dump_to_file(self):
        timestamp = time.strftime("%Y%m%d", time.gmtime())
        logger.info(f"Saving result onto file: {timestamp}.md")
        with open(f"{timestamp}.md", "w") as dest:
            dest.write(self.render_agenda())

    def print_result(self):
        print(self.render_agenda())

if __name__ == '__main__':
    agenda = AgendaBuilder()
    agenda.run()

