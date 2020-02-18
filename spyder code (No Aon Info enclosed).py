#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import re

from bs4 import BeautifulSoup
from splinter import Browser


# In[ ]:

#URL list of for bbc news homepages, all with same structure
#I used the smaller list for testing
bbc_urls_full = ("https://www.bbc.com/news/world",
                "https://www.bbc.com/news/uk",
                "https://www.bbc.com/news/business",
                "https://www.bbc.com/news/technology",
                "https://www.bbc.com/news/science_and_environment",
                "https://www.bbc.com/news/stories",
                "https://www.bbc.com/news/health",
                "https://www.bbc.com/news/special_reports",
                "https://www.bbc.com/news/reality_check")

bbc_urls = ["https://www.bbc.com/news/world"]

#starter urls for financial times.com
ft_urls = ("https://www.ft.com/world",
           "https://www.ft.com/technology")

# In[ ]:

'''
In attempt to make scraper generalizable, I use dictionaries that target
specific divs for each site. Each site will have a num of different divs
I place the common elements in dicts below
'''

'''
The keys specify the target: div, headline, description, link(to article)
the hl, and link elements are lists, as I need to specify the element +
the class
'''

#top story div
bbc_div_1 = {"div": '="gs-c-promo-body gs-u-mt@xxs gs-u-mt@m gs-c-promo-body--primary gs-u-mt@xs gs-u-mt@s gs-u-mt@m gs-u-mt@xl gel-1/3@m gel-1/2@xl gel-1/1@xxl',
               "hl": ["h3","gs-c-promo-heading__title gel-paragon-bold gs-u-mt+ nw-o-link-split__text"],
               "desc": "p",
               "link": ["a", "gs-c-promo-heading__title gel-paragon-bold gs-u-mt+ nw-o-link-split__text"]
               }

#second to top stories
bbc_div_2 = {"div": "gs-c-promo-body gs-u-mt@xxs gs-u-mt@m gs-c-promo-body--flex gs-u-mt@xs gs-u-mt0@xs gs-u-mt@m gel-1/2@xs gel-1/1@s",
           "hl": ["h3", "gs-c-promo-heading__title gel-pica-bold nw-o-link-split__text"],
           "desc": "p",
           "link": ["a", "gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-pica-bold nw-o-link-split__anchor"]
           }

#the other stories
bbc_div_3 = {"div": "gs-c-promo-body gs-u-mt@xxs gs-u-mt@m gs-u-mt@m gel-1/2@xs gel-1/1@m gs-c-promo-body--flex" ,
             "hl": ["h3","gs-c-promo-heading__title gel-pica-bold nw-o-link-split__text"],
             "desc": "na",
             "link": ["a", "gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-pica-bold nw-o-link-split__anchor"],
                 }


#currently the most common story division, have yet to add the top story dict
ft_div_1 = {"div": "o-teaser__content",
          "hl": ["a", "js-teaser-heading-link"],
          "desc": ["p", "o-teaser__standfirst"],
          "link": ["a", "js-teaser-heading-link"],
          "tag": ["a", "o-teaser__tag"]
         }


#This is a similar style dict, but is used to target the text and/or tag
#some articles don't have tags
ft_text = {"text": ["div", "article__content-body n-content-body js-article__content-body"],
           "tag": ["a", "n-content-tag n-content-tag--medium n=content-tag--brand"]}

bbc_text = {"text": ["div", "story-body__inner"],
           "tag": ["li", "tags-list__tags"]}

#created a list of these dicts to pass through the function
#For now I'm reserving the last entry in the lit for the text dict
#even I can tell this is dumb, but I'll fix later.
bbc_dicts = [bbc_div_1, bbc_div_2, bbc_div_3, bbc_text]
ft_dicts = [ft_div_1, ft_text]

# In[ ]:


# In[ ]:


#starts the splinter browser session
def start_browser():
    
    #points to the required chromedriver
    exe_path ="C:/Users/pat/.spyder-py3/chromedriver.exe"
    browser = Browser("chrome", executable_path = exe_path)
    
    return browser



# In[ ]:

#Function to extract divs specifed by the relevant dictionary
#This is used inside the total scraper function (where page_soup is generated)
def div_extractor(page_soup, d_dict):
    
    #initializing lists for headlines, descriptions, links
    hl_list = []
    desc_list = []
    link_list = []
    
    #all instances of the relevant div
    div_html = page_soup.find_all("div", d_dict["div"])
    
    #Used try-except as it will ail in fewer instnces than succeed
    #read that it is more effiicent than if-then in that cast
    #Some divs won't have descriptions, links or whatever-don't want it to fail
    for div in div_html:
        
        #element = dict[0], class_= dict[2]
        try:
            hl_ele = div.find(d_dict["hl"][0], d_dict["hl"][1])
            hl = hl_ele.get_text()
        except:
            hl = "not available"
        finally:
            hl_list.append(hl)
            
        #adds prefix to link. (the hrefs are truncatd, not functional links)
        try:
            link_ele = div.find(d_dict["link"][0], d_dict["link"][1])
            link = link_ele["href"]
            if d_dict in bbc_dicts:
                link = "https://bbc.com"+link
            else:
                link = "https://ft.com"+link
        except:
            link = "not available"
        finally:
            link_list.append(link)

        #sometimes desc has a class, sometimes not
        try:
            desc_ele = div.find(d_dict["desc"][0], d_dict["desc"][1])
            desc = desc_ele.get_text()
        except:
            try:
                desc_ele = div.find(d_dict["desc"][0])
                desc = desc_ele.get_text()
            except:
                desc = "not available"
        finally:
            desc_list.append(desc)
         
    
    div_df = pd.DataFrame({"headline": hl_list,
                            "description": desc_list,
                            "article_link": link_list})
    
    return div_df


# In[ ]:

#this part is used when the scraper visits the article link generated
#by the function above
def article_scraper(url, text_dict):
    
    #for whatever reason, I needed to start another browser session for each
    #article, not sure why
    browser = start_browser()
    
    browser.visit(url)
    
    page_soup = BeautifulSoup(browser.html, "html5lib")
    
    #essentially the same process as above. Difference is I assumed
    #all articles have the same structure. I tink video pages have different
    #structures, but I don't care about them yet.
    try:
        div_html = page_soup.find(text_dict["text"][0], text_dict["text"][1])
        text_html = div_html.find_all("p")
        text = [p.get_text() for p in text_html]
    except:
        text = "potentially different structure"
    
    #some articles have tags, others don't. If it has a tag, I want it
    #If it doesn't have a tag, it's not the end of the world
    try:
        tag_html = page_soup.find(text_dict["tag"][0], text_dict["tag"][1])
        tag = tag_html.get_text()
    except:
        tag = "not available"
        
    return text, tag
    
        
    


# In[ ]:
'''
This is the main function, that integrates the others. Takes your list of
starter urls and your dictionary list. right now I've only tested it on
bbc sites, and haven't changed it so that it can take a list of all
urls. Aim is to take a list of urls from different sites and use the correct
dictionaries only.

I am definitely going to change it though, because splinter is much slower
than the requests package. I only needed splinter for ft.com scraping,
as it has a login page with lots of javascript and stuff that I couldn't
get passed using requests.

Thinking that I'll have website classes, and one of the attributes will be
"login needed" or whatever --> if yes, will use splinter, if not -- requests

'''


#I don't know how to generalize logins, so I'll just put the ft_login code
#in here for now

def news_scraper(url_list, dict_list):
    
    #initializes a dataframe into which the divs will be eztracted into
    total_cols = ["headline", "description", "article_link", "page_url"]
    total_df = pd.DataFrame(columns = total_cols)
    
    browser = start_browser()
    
    
    if url_list == ft_urls:
        login_url = "https://accounts.ft.com/login?location=https%3A%2F%2Fwww.ft.com"
        
        #This is my login for ft.com only so don't get any ideas
        #I had to change it because when I was testing the code, ft.com
        #recgnized I was using a bot or whatever and forced me to reset.
        email = "x18124917@student.ncirl.ie"
        password = "Please_Let_Me"
        
        #visits the page, fills in email, click "next" to reveal password
        #clicks "sign in using password". as it#s easier than NCI sso.
        #enters passwords and clicks sing-on.
        browser.visit(login_url)
        browser.find_by_id("enter-email").fill(email)
        browser.find_by_id("enter-email-next").click()
        browser.find_by_id("sign-in-with-ft-creds").click()
        browser.find_by_id("enter-password").fill(password)
        sign_in_path = "/html/body/div[2]/div[2]/div/form/div[3]/button"
        browser.find_by_xpath(sign_in_path).click()
            
    
    
    
    #Visits each url and runs the div extractor on it
    for url in url_list:
        
        browser.visit(url)
        page_html = browser.html
        page_soup = BeautifulSoup(page_html, "html5lib")
        
        #each "homepage" has multiple types of div --> cycle over them (except
        #for the last one, which is the spcial text 1, will change later)
        for dictionary in dict_list[:-1]:
            
            #calls the div_extractor fx
            div_df = div_extractor(page_soup, dictionary)
            div_df["page_url"] = url
            total_df = total_df.append(div_df)

    '''            
    removes tge rows where the follow-up links aren't available
    Any article without a headline is probably urnreliable too, or not useful
    This is because I weight the headline words higher in the text analysis
    then removes duplicates, because I don't want to visit and extract
    an article page I've already done --> waste of time
    '''
    new_df = total_df[total_df["article_link"] != "not available"]
    new_df = new_df[new_df["headline"] != "not available"]
    new_df = new_df.drop_duplicates()
    
    #Becuse of all the appending, the index got messed up.
    new_df = new_df[total_cols]
    new_df = new_df.reset_index(drop=True)
    
    #setting the column with the follow-up urls as the target of next function
    target = new_df["article_link"]
    
    #The lambda fees eachs of the follow-up urls into the article_scraper fs
    #And puts the text into the full_text col, and the tag into the tag col
    new_df["full_text"], new_df["tag"] = target.apply(lambda x: article_scraper(x, dict_list[-1]))
    
    #writes to a csv (temp name)
    new_df.to_csv(r"C:\Users\pat\.spyder-py3\bbc_articles.csv")
    
    return new_df
    

#Will upload the text analysis part separately, as I did the analysis on
#output of the earlier form of the scraper (didn't include ft.com at that
#point)           

