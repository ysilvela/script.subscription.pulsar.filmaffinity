# coding: utf-8
import xbmcaddon
import xbmc
import re
import subscription

# this read the settings
settings = subscription.Settings()
# define the browser
browser = subscription.Browser()
language = xbmcaddon.Addon().getSetting('language')
xbmc.log('[service.subscription] Language selected: ' + language)
if language == "es":
    url_search = "http://www.filmaffinity.com/es/countcat.php?id=new_th_es"
    xbmc.log('[service.subscription] Using language selection')
else:
    url_search = "http://www.filmaffinity.com/en/topcat_DVD_VID_US.html"
    xbmc.log('[service.subscription] Using default language selection')
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
