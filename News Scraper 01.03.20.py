#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import nltk
import nltk.stem
import re


# In[ ]:


#List of the BBC homepages I'll be getting first links from
bbc_urls_full = ("https://www.bbc.com/news/world",
                "https://www.bbc.com/news/uk",
                "https://www.bbc.com/news/business",
                "https://www.bbc.com/news/technology",
                "https://www.bbc.com/news/science_and_environment",
                "https://www.bbc.com/news/health")


# In[ ]:


#Ccreating a dataframe of the homepage url + html/soup
urls = []
htmls = []

for url in bbc_urls_full:

    req = requests.get(url)
    content = req.content
    page_soup = BeautifulSoup(content, 'html.parser')
    urls.append(url)
    htmls.append(page_soup)

html_df = pd.DataFrame({"base_url": urls,
                        "html": htmls})

html_df.to_csv("bbc_homepages.csv", index = False)


# In[ ]:


'''
With the html for each page downloaded, needed to identify
and extract the objects of interest. For news sites, these
were divisins typically with a headline, and a link. Some
headlines were stored separate to links (e.g specials) and some
had descriptions while others not. The descriptions were pretty
useless, as I planned to extract the full text for each article

As the objects had similar structures, I defined dictionaries for
each, and then a dataframe for all of them. I found it easier to
add objects of interest this way.
'''

#the links are stored in the headlines (most cases).They are
#truncated by default, hence appending bbc.com etc.
top_story = {"name": "top_story",
             "url_base": "http://bbc.com",
             "div_class": "gs-c-promo-body gs-u-mt@xxs gs-u-mt@m gs-c-promo-body--primary gs-u-mt@xs gs-u-mt@s gs-u-mt@m gs-u-mt@xl gel-1/3@m gel-1/2@xl gel-1/1@xxl",
             "hl_ele": "a",
             "hl_class": "gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-paragon-bold gs-u-mt+ nw-o-link-split__anchor"
                 }

second_stories = {"name": "second_story",
                  "url_base": "http://bbc.com",
                  "div_class": "gs-c-promo-body gs-u-mt@xxs gs-u-mt@m gs-c-promo-body--flex gs-u-mt@xs gs-u-mt0@xs gs-u-mt@m gel-1/2@xs gel-1/1@s",
                  "hl_ele": "a",
                  "hl_class": "gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-pica-bold nw-o-link-split__anchor"
                  }

third_stories = {"name": "third_story",
                 "url_base": "http://bbc.com",
                 "div_class": "gs-c-promo-body gs-u-mt@xxs gs-u-mt@m gs-u-mt@m gel-1/2@xs gel-1/1@m gs-c-promo-body--flex",
                 "hl_ele": "a",
                 "hl_class": "gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-pica-bold nw-o-link-split__anchor"
                 }

bottom_stories = {"name": "bottom_story",
                  "url_base": "http://bbc.com",
                  "div_class": "gs-o-media__body",
                  "hl_ele": "a",
                  "hl_class": "qa-heading-link lx-stream-post__header-link"
                  }

#the headline doesnt really work for these, will get the headlines from the
#full text articles. they are in different divs on homepage idk why. the links
#are also in a separate part. I just call it hl_ele here so don't need to change
#functions.
bottom_specials = {"name": "bottom_specials",
                   "url_base": "no_url",
                   "div_class": "lx-stream-post-body",
                   "hl_ele": "a",
                   "hl_class": "na"
                   }


dicts = [top_story, second_stories, third_stories,
         bottom_stories, bottom_specials]

dict_df_cols = ["name", "url_base", "div_class",
                   "hl_ele", "hl_class"]
dict_df = pd.DataFrame(columns = dict_df_cols)

dict_df = dict_df.append(dicts, ignore_index = True)


# In[ ]:


#This function will take in a single HTML string/cell and
#extract the relevant info from each object (headling, link etc)

def div_extractor(html, dictionary):
    
    headlines = []
    fulltext_links = []
    
    #will cycle through each of the dictionaries to find divisions
    #of each type
    divs = html.find_all("div", class_= dictionary["div_class"])
    
    for div in divs:
        
        #tries to get the headline. if it doesn't have a class, tries without
        #each always has a headline. if not, it'l be flagged "revisit"
        try:
            headline = div.find(dictionary["hl_ele"], class_= dictionary["hl_class"])
        except:
            headline = div.find(dictionary["hl_ele"])

        try:
            headline_text = headline.get_text()
        except:
            headline_text = "revisit"
            
        finally:
            headlines.append(headline_text)

        #tries to extract the link from the headline and then adds on
        #the url base to make a functional link
        try:
            fulltext_link = str(dictionary["url_base"])+str(headline["href"])
        except:
            fulltext_link = "error"
        finally:
            fulltext_links.append(fulltext_link)

        
    
    output_df = pd.DataFrame({"headline": headlines,
                              "fulltext_link": fulltext_links})
    
    
    return output_df


# In[ ]:


#main function for this part, it's called on the homepage df
#and takes in the dictionary df
def home_div_extract(html_dataframe, dict_df):
    
    cols = ["headline", "fulltext_link", "story_type", "homepage"]
    homepage_df = pd.DataFrame(columns = cols)
    
    
    for i in range(len(html_dataframe)):
        #just for a reference for where article appeared.
        #removes the bbc part --> makeshift page tag
        base_url = html_dataframe["base_url"][i]
        homepage = base_url.replace("https://www.bbc.com/news/", "")
        #isolates the html
        html = html_dataframe["html"][i]
        
        #when you read the html back in from csn, need to turn it to soup again
        soup = BeautifulSoup(html, "html.parser")
        
        #feeds the html and each dictionary into the div extractor
        for index in range(len(dict_df)):
            
            dictionary = dict_df.iloc[index]
            div_output = div_extractor(soup, dictionary)
            div_output["story_type"] = dictionary["name"]
            div_output["homepage"] = homepage
            homepage_df = homepage_df.append(div_output)    
    
    return homepage_df


# In[ ]:


#Lot of them will have errors, because the special stories and the
#bottom stories shared a div class, but then had entirely different
#structures. culled the ones with errors/missing links.
homepage_df = home_div_extract(html_df, dict_df)
homepage_df.index = range(len(homepage_df))
homepage_df = homepage_df[homepage_df["fulltext_link"] != "error"]

homepage_df.to_csv("bbc_homepage_divs.csv", index = False)


#summarizing the df to remove duplicates. but wanted to also
#know how many times each article appears. might use this later
#to weight the analysis toward articles that appear many times.
fulltext_links = pd.read_csv("bbc_homepage_divs.csv")
fulltext_links["occurrences"] = 1
summed_links = fulltext_links.groupby(["headline", "fulltext_link"],
                                      as_index = False).sum()


# In[ ]:


#function that visits the full text links extracted above
#and gets the html for these. puts into a df
def article_scraper(summed_df):
    
    article_soups = []
    
    for i in range(len(summed_df)):
        req = requests.get(summed_df["fulltext_link"][i])
        content = req.content
        req_soup = BeautifulSoup(content, "html.parser")
        article_soups.append(req_soup)
        
    
    summed_df["article_soup"] = article_soups
         
    return summed_df


# In[ ]:


#some articles had different headline times.
hl_ele = "h1"
hl_class1 = "story-body__h1"
hl_class2 = "vxp-media__headline"    

#gets the headline
def hl_extractor(soup):
    
    hl_soup = soup.find(hl_ele, class_= hl_class1)
    try:
        headline = hl_soup.get_text()
    except:
        try:            
            hl_soup = soup.find(hl_ele, class_= hl_class2)
            headline = hl_soup.get_text()
        except:
            headline = "replace"
            
    return headline


# In[ ]:


#The special objects from earlier had headlines disconnected
#from their links + full texts etc. This below takes the headline
#in the fulltext part as the actual headline. Also, some of the 
#headlines not extracted from article already had hl from earlier.
temp = articles["article_soup"].apply(lambda x: hl_extractor(x))
articles["headline 2"] = temp
temp = articles["headline"][articles["headline 2"] == "replace"]
articles["headline 2"][articles["headline 2"] == "replace"] = temp


# In[ ]:


#Each article had tag list at bottom. Some had a main tag at the top
#I decided to let the latter articles duplicate tags. might be useful 
#for weighting of topics later.
tag_list_ele = "li"
tag_list_class = "tags-list__tags"
tag_ele = "a"

def tag_list_extractor(soup):
    
    tags = []
    
    tag_soup = soup.find_all(tag_list_ele, class_= tag_list_class)
    
    for group in tag_soup:
        try:
            text = group.get_text()
        except:
            text = "no tags"
        finally:
            tags.append(text)

    return tags


# In[ ]:


temp = articles["article_soup"].apply(lambda x: tag_list_extractor(x))
articles["tags"] = temp


# In[ ]:


#lots of different fulltext structures. easier to do them in a list
story_ele = "div"
story_class1 = "story-body__inner"
story_class2 = "vxp-media__summary"
story_class3 = "story-body sp-story-body gel-body-copy"
story_class4 = "lx-stream-post-body"
class_list = [story_class1, story_class2, story_class3, story_class4]

def text_extractor(soup):
    
    paragraphs = []
    
    counter = 0
    #loops through the story classes until it finds the right one
    while len(paragraphs) == 0 and counter < len(class_list):
        
        text_soup = soup.find_all(story_ele, class_= class_list[counter])
        counter += 1
        for paragraph in text_soup:
            text = paragraph.get_text()
            paragraphs.append(text)
            
    return paragraphs
    

temp = articles["article_soup"].apply(lambda x: text_extractor(x))
articles["fulltext"] = temp


# In[ ]:


#removes the soups as they serve no purpose for the analysis part
articles.to_csv("Completed df.csv")

no_soups = ["headline 2", "occurrences", "tags", "fulltext_link", "fulltext"]
no_soup_df = articles[no_soups]
no_soup_df.to_csv("Completed df.csv")


# In[ ]:


analysis_df = pd.read_csv("Completed df.csv")

def clean_text(text):
    
    #specifying the patterns I want to get rid of:
    #lots of "\n", credit for images  with names, then lots of
    #advert info between /**/ etc. removes punctuation.
    ex_pats = [r"\\n*", "Image copyright.*?Image caption",
               "/\*\*/.*?/\*\*/", '[^\w\s]']
    
    for pat in ex_pats:
        text = re.sub(pat, " ", str(text))
    
    #removes single letter words and s' when punct removed
    text = ' '.join( [w for w in text.split() if len(w)>1] )
    
    tokens = nltk.word_tokenize(text.lower())
    
    
    lemmatizer = nltk.stem.WordNetLemmatizer()
    lemmas = [lemmatizer.lemmatize(token) for token in tokens]
    
    stops = set(nltk.corpus.stopwords.words("english"))
    
    no_stops = [word for word in lemmas if word not in stops]
    
    return no_stops


temp = analysis_df["fulltext"].apply(lambda x: clean_text(x))
analysis_df["clean_text"] = temp


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




