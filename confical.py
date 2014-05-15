#!/usr/bin/python
from bs4 import BeautifulSoup
from datetime import date
import datetime
from icalendar import Calendar, Event
import pytz
import string
import urllib.request, urllib.error, urllib.parse
import re

DEBUG = False


start_index_conf_shortnames = 2

if DEBUG:
    OUTFILE = '/tmp/conferences.ics'
else:
    OUTFILE = '/var/www/confical/conferences.ics'


class Conf():
    def __init__(self, title, deadline, description, venue, dates=("","")):
        self.title = title
        self.deadline = deadline
        self.description = description
        self.venue = venue
        self.dates = dates

    def getDescription(self):
        string = self.description + " at " 
        if self.venue:
            string += self.venue 
        string += "\n From: " + self.dates[0].strftime('%d.%m.%Y') 
        if len(self.dates)==2:
            string += " to: "+ self.dates[1].strftime('%d.%m.%Y')
        return string
    
    def __repr__(self):
        return self.title + ": " + str(self.deadline.day) + "." + str(self.deadline.month)

    def isValid(self):
        return True
#        return (self.deadline!="None") and (self.dates[1]!="None")

class Website(object):
    def parse(self):
        site = self.download()
        conferences = self.parseConferencesFromString(site)
        return conferences

class Friedetzky(Website):
    URL = ' http://www.dur.ac.uk/tom.friedetzky/conf.html'

    def download(self):
        response = urllib.request.urlopen(self.URL)
        html = response.read()
        return html
    
    def parseConferencesFromString(self,string):
        soup = BeautifulSoup(string)
        header = [ x for x in soup.findAll('ul')]
        confs = [ x for x in header[0] ]
        confs_cleaned = [str(x).strip() for x in confs if x]
        
        conferences = []
        for x in confs_cleaned:
            if x and len(x.strip())!=0:
                
                tag = re.search("<strong>(.*?)</strong>", x).group(1)
                longname = re.search("</strong>\n.*?\((.*?)\)", x).group(1)
                deadline = re.search("Submission deadline: <b>(.*?)</b>", x).group(1)
                dates_and_location = re.search("Conference dates: (.*?)<br.*\n(.*?)<br", x)
                date_and_location = re.search("Conference date: (.*?)<br.*\n(.*?)<br", x)
                dates = dates_and_location.group(1) if dates_and_location else date_and_location.group(1)
            
                location = dates_and_location.group(2) if dates_and_location else date_and_location.group(2)
                link = re.search("More info: <a href.*>(.*)</a><p>", x).group(1)

                #convertdates
                deadline_date = datetime.datetime.strptime(deadline, "%B %d, %Y")
                datessplit = re.search("(.*) - (.*)", dates)
                if dates_and_location:
                    startconf_date = datetime.datetime.strptime(datessplit.group(1), "%B %d, %Y")
                    endconf_date = datetime.datetime.strptime(datessplit.group(2), "%B %d, %Y")
                    conf = Conf(tag, deadline_date, longname, location, (startconf_date, endconf_date))
                else:
                    conf = Conf(tag, deadline_date, longname, location, (startconf_date,))
                    #print(conf)
                conferences.append(conf)
        #build conferences
        return conferences




class Farishi(Website):
    URL = 'http://cs.yazd.ac.ir/farshi/conf.html'
    def download(self):
        # the real download is complicated because frames are web2.0 and static html is even 3.0
        with open('test-farishi.html', 'r') as f:
            thefile = f.read()
        return thefile

    def parseConferencesFromString(self, string):
#        print(string)
        
        parsed_html = BeautifulSoup(string)
        trs = parsed_html.body.findAll('tr')
        conferences = []
        for elem in trs[2:]:              #the first two are junk tags
            tds = elem.findAll('td')
            #print(tds.decode("utf8"))

            for x in tds:
                print(x.text.encode("utf8"))
            print("done")
            tag = tds[0].text
            try: 
                deadline_date = datetime.datetime.strptime(tds[1].text, "%d %b %Y")
            except:
                deadline_date = datetime.datetime.strptime(tds[1].text, "%d %B %Y")
            longname = ""
            location = ""
#            notification = datetime.datetime.strptime(tds[2].text, "%d %B %Y")
            datessplit = re.search("(.*) - (.*)", tds[3].text)
            #startconf_date = datetime.datetime.strptime(tds[2].text, "%d %b %Y")
            #endconf_date = datetime.datetime.strptime(tds[3].text, "%d %b %Y")
            
            
            conf = Conf(tag, deadline_date, longname, location)
            conferences.append(conf)
            
    
        
        return conferences


        #        table = re.findall("<tr>(?iLmsux)*</tr>", string)
        return table
    

def gatherTwo(list):
    list1 = [x for i,x in enumerate(list) if i%2 == 0]
    list2 = [x for i,x in enumerate(list) if i%2 == 1]

    gatherer = [(x,y) for x,y in zip(list1,list2)]
    return gatherer
    

    
def constructCalendar(conferences):
    cal = Calendar()
    cal.add('prodid', '-//conferences//mxm.dk')
    cal.add('version', '2.0')

    for c in conferences:
        #print(c)
#        if c.isValid():
        event = Event()
        event.add('summary', string.upper(c.title) + ' Deadline')
        event.add('description',  c.getDescription())
            
        year = c.deadline.year
        month = c.deadline.month
        day = c.deadline.day
        event.add('dtstart', datetime.datetime(year, month, day, 0, 0, tzinfo=pytz.utc))
        event.add('dtend', datetime.datetime(  year, month, day, 20, 0, tzinfo=pytz.utc))
        event.add('dtstamp', datetime.datetime(year, month, day, 0, 0, tzinfo=pytz.utc))
        cal.add_component(event)

    return cal

def writeCal(calendar):
    with open(OUTFILE, 'wb') as f:
        f.write(calendar.to_ical())

website = Friedetzky()
tmp = website.parse()
writeCal(tmp)
# website = Farishi()
# tmp = website.parse()
# print(tmp)


