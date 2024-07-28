#! /usr/bin/python3

import os
import sys
import time
import argparse
import requests
import re
import json

GITHUB = "https://github.com"
PAUTAS = f"{GITHUB}/helioloureiro/canalunixloadon/tree/master/pautas"
RAWGITHUB = "https://raw.githubusercontent.com"


def curl(url):
    req = requests.get(url)
    if req.status_code == 200:
        return req.text
    raise Exception(f"Failed to fetch content from {url}")

def getHref(line):
    """
    <span class="css-truncate css-truncate-target d-block width-fit"><a class="js-navigation-open Link--primary" title="20220211.md" data-pjax="#repo-content-pjax-container" href="/helioloureiro/canalunixloadon/blob/master/pautas/20220211.md">20220211.md</a></span>
    """
    line = re.sub(".*href=\"", "", line)
    line = re.sub("\">.*", "", line)
    return line

def unblob(url):
    return re.sub("/blob", "", url)

def getJsonFromLine(line: str) -> str:
    line = re.sub("</.*>", "", line)
    line = re.sub(".*>", "", line)
    return json.loads(line)

class Pautas(object):
    def __init__(self): None

    def GetLatest(self):
        links = []
        pautas = curl(PAUTAS)
        dataJson = {}
        for line in pautas.splitlines():
            if not re.search("react-app.embeddedData", line):
                continue
            dataJson = getJsonFromLine(line)
            break
        print(json.dumps(dataJson, indent=4))

        content = []
        for line in dataJson["payload"]["tree"]["items"]:
            if re.search(r"\d+.md", line["name"]):
                content.append(line["name"])
        content = sorted(content)
        print(content)

        self.latest = content[-1]
        self.latestURL = f"{RAWGITHUB}/helioloureiro/canalunixloadon/master/pautas/{self.latest}"
        print("latest  :", self.latestURL)
        #print("expected: https://raw.githubusercontent.com/helioloureiro/canalunixloadon/master/pautas/20220210.md")

    def GetContentFromRaw(self, url : str) -> dict:
        body = curl(url)
        sections = {}
        topics = body.split("\n\n")
        for tpc in topics:
            lines = tpc.splitlines()
            title = None
            if re.search("========", lines[1]):
                title = lines[0]
            elif re.search("=========", lines[2]):
                title = lines[1]

            if title is None:
                print("Empty body:", tpc) 
                continue
            print("Adding section:", title)

            content = []
            for line in lines:
                if line.startswith("*"):
                    content.append(line)
                    continue
            sections[title] = content
        return sections


    def FetchLatestContent(self):
        self.GetLatest()
        data = self.GetContentFromRaw(self.latestURL)
        return data

class NewFilter(object):
    def __init__(self):
        self.ParseArgs()


    def ParseArgs(self):
        parser = argparse.ArgumentParser(description='Parse last content out from large content for Unix Load On.')
        parser.add_argument('--content', dest='content',
                            help='File with topics from last talkshow.')
        parser.add_argument('--webcontent', dest='webcontent',
                            help='URL with content to be filtered out')

        args = parser.parse_args()
        self.contentFile = args.content
        self.webURL = args.webcontent

        if self.webURL is None or self.webURL == "latest":
            pauta = Pautas()
            pauta.GetLatest()
            self.webURL = pauta.latestURL


    def CalculateNextDay(self) -> str:
        lastDay = os.path.basename(self.webURL)
        lastDay = re.sub(r"\.md", "", lastDay)
        year = lastDay[:4]
        month = lastDay[4:6]
        day = lastDay[6:]
        #print("Lastday:", lastDay)
        #print("year:" ,year)
        #print("month:", month)
        #print("day:", day)
        timestamp = time.strftime("%H:%M:%S", time.gmtime())
        hour, minute, second = timestamp.split(":")
        tup = (int(year), int(month), int(day), int(hour), int(minute), int(second), 0, 0, 0)
        time_sec = time.mktime(tup)
        time_sec += 15 * 60 * 60 # 2 weeks

        return time.strftime("%Y%m%d", time.gmtime(time_sec))

    def Out(self):
        pauta = Pautas()
        data = pauta.GetContentFromRaw(self.webURL)
        output = ""
        for section in data:
            secondLine = "=" * len(section)
            output += section + "\n"
            output += secondLine + "\n"
            if re.search("Assuntos", section):
                output += "\n"
                continue
            output += "\n".join(data[section])
            output += "\n\n"
        print(output)
        timestamp = self.CalculateNextDay()
        print("Next episode:", timestamp)
        with open(f"{timestamp}.md", "w") as dest:
            dest.write(output)
        print(f"Saved into: {timestamp}.md")

if __name__ == '__main__':
    filter = NewFilter()
    filter.Out()

