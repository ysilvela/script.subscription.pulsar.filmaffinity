# coding: utf-8
import re
import subscription

# this read the settings
settings = subscription.Settings()
# define the browser
browser = subscription.Browser()

if self.language == "es":
    url_search = "http://www.filmaffinity.com/es/countcat.php?id=new_th_es"
else:    
 url_search = "http://www.filmaffinity.com/en/topcat_DVD_VID_US.html"
listing = []
ID = []  # IMDB_ID or thetvdb ID
if browser.open(url_search):
    data = browser.content.replace('</a>', '')
    listing =[item[1] for item in re.findall('<div class="mc-title">(.*?)>(.*?)<',data)]
# else:
#     provider.log.error('>>>>>>>%s<<<<<<<' % browser.status)
#     provider.notify(message=browser.status, header=None, time=5000, image=settings.icon)
#     results = []
subscription.integration(listing, ID,'MOVIE', settings.movie_folder)
