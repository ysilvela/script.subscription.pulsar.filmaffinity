# library to access URL, translation title and filtering
__author__ = 'mancuniancol'
import re 
import xbmcaddon
import xbmc
import xbmcgui
import os

class Settings:
    def __init__(self):
        self.settings = xbmcaddon.Addon()
        self.id_addon = self.settings.getAddonInfo('id')  # gets name
        self.icon = self.settings.getAddonInfo('icon')
        self.name_provider = self.settings.getAddonInfo('name')  # gets name
        self.name_provider = re.sub('.COLOR (.*?)]', '', self.name_provider.replace('[/COLOR]', ''))
        self.movie_folder = ''
        self.show_folder = ''
        while self.movie_folder =='' and self.show_folder == '':
            self.movie_folder = self.settings.getSetting('movie_folder')
            self.show_folder = self.settings.getSetting('show_folder')
            if self.movie_folder == '' or self.show_folder == '':
                self.settings.openSettings()
        self.clear_database = self.settings.getSetting('clear_database')
        if self.clear_database == 'true':
            path = xbmc.translatePath('special://temp')
            if os.path.exists(path + 'pulsar-subscription-data.db'):
                os.remove((path + 'pulsar-subscription-data.db'))
            self.settings.setSetting('clear_database', 'false')
        self.dialog = xbmcgui.Dialog()

class Browser:
    def __init__(self):
        import cookielib
        self._cookies = None
        self.cookies = cookielib.LWPCookieJar()
        self.content = None
        self.status = None

    def create_cookies(self, payload):
        import urllib
        self._cookies = urllib.urlencode(payload)

    def open(self,url):
        import urllib2
        result = True
        if self._cookies is not None:
            req = urllib2.Request(url,self._cookies)
            self._cookies = None
        else:
            req = urllib2.Request(url)
        req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36')
        req.add_header("Accept-Encoding", "gzip")
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))#open cookie jar
        try:
            response = opener.open(req)  # send cookies and open url
            #borrow from provider.py Steeve
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                self.content = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response.read())
            else:
                self.content = response.read()
            response.close()
            self.status = 200
        except urllib2.URLError as e:
            self.status = e.reason
            result = False
        except urllib2.HTTPError as e:
            self.status = e.code
            result = False
        return result

    def login(self, url, payload, word):
        result = False
        self.create_cookies(payload)
        if self.open(url):
            result = True
            data = self.content
            if word in data:
                self.status = 'Wrong Username or Password'
                result = False
        return result


# find the name in different language
def translator(imdb_id, language):
    import unicodedata
    import json
    browser1 = Browser()
    keywords = {'en': '', 'de': '', 'es': 'espa', 'fr': 'french', 'it': 'italian', 'pt': 'portug'}
    url_themoviedb = "http://api.themoviedb.org/3/find/%s?api_key=8d0e4dca86c779f4157fc2c469c372ca&language=%s&external_source=imdb_id" % (imdb_id, language)
    if browser1.open(url_themoviedb):
        movie = json.loads(browser1.content)
        title0 = movie['movie_results'][0]['title'].replace(u'\xf1', '*')
        title_normalize = unicodedata.normalize('NFKD', title0)
        title = title_normalize.encode('ascii', 'ignore').replace(':', '')
        title = title.decode('utf-8').replace('*', u'\xf1').encode('utf-8')
        original_title = movie['movie_results'][0]['original_title']
        if title == original_title:
            title += ' ' + keywords[language]
    else:
        title = 'Pas de communication avec le themoviedb.org'
    return title.rstrip()


class TV_Show():
    def __init__(self, name):
        import json
        import urllib
        browser = Browser()
        if browser.open('http://localhost:65251/shows/search?q=%s' % urllib.quote(name)):
            data = json.loads(browser.content)
            self.code = data['items'][0]['path'].replace('plugin://plugin.video.pulsar/show/','').replace('/seasons','')
            browser.open('http://localhost:65251/show/%s/seasons' % self.code)
            data = json.loads(browser.content)
            seasons =[]
            for item in data['items']:
                seasons.append(int(item['label'].replace('Season ','').replace('Specials', '0')))
            seasons.sort()
            episodes = []
            for season in seasons:
                browser.open('http://localhost:65251/show/%s/season/%s/episodes' % (self.code, season))
                data = json.loads(browser.content)
                episodes.append(len(data['items']))
            if len(seasons) > 0:
                self.first_season = seasons[0]
                self.last_season = seasons[-1]
            else:
                self.first_season = 0
                self.last_season = 0
            self.last_episode = episodes
        else:
            self.code =None


class TV_Show_code():
    def __init__(self, code):
        import json
        import urllib
        browser = Browser()
        self.code = code
        browser.open('http://localhost:65251/show/%s/seasons' % self.code)
        data = json.loads(browser.content)
        seasons =[]
        for item in data['items']:
            seasons.append(int(item['label'].replace('Season ','').replace('Specials', '0')))
        seasons.sort()
        episodes = {}
        for season in seasons:
            browser.open('http://localhost:65251/show/%s/season/%s/episodes' % (self.code, season))
            data = json.loads(browser.content)
            episodes[season] = len(data['items'])
        if len(seasons) > 0:
            self.first_season = seasons[0]
            self.last_season = seasons[-1]
        else:
            self.first_season = 0
            self.last_season = 0
        self.last_episode = episodes


class Movie():
    def __init__(self, name):
        import json
        import urllib

        if ')' in name and '(' in name:
            try:
                year_movie = int(name[name.find("(")+1:name.find(")")])
                name = name.replace('(%s)' % year_movie, '').rstrip()
            except:
                year_movie = None
        else:
            year_movie = None
        browser = Browser()
        if browser.open('http://localhost:65251/movies/search?q=%s' % urllib.quote(name)):
            data = json.loads(browser.content)
            if len(data['items']) > 0:
                if year_movie is not None:
                    for movie in data['items']:
                        label = movie['label']
                        path = movie['path']
                        if movie['info'].has_key('year'):
                            year = movie['info']['year']
                        else:
                            year = 0000
                        if year == year_movie:
                            break
                else:
                    label = data['items'][0]['label']
                    path = data['items'][0]['path']
                    year = data['items'][0]['info']['year']
                self.code = path.replace('plugin://plugin.video.pulsar/movie/', '').replace('/play', '')
                self.label = label
            else:
                self.code = None
                self.label = name
        else:
            self.code = None
            self.label = name


def integration(listing, ID, type_list, folder, silence=False):
    import shelve

    dialog = xbmcgui.Dialog()
    action = xbmcaddon.Addon().getSetting('action')  # gets action
    total = len(listing)
    if total > 0:
        if not silence:
            answer = dialog.yesno('Pulsar list integration: %s items\nDo you want to subscribe this list?' % total, '%s' % listing)
        else:
            answer = True
        if answer:
            pDialog = xbmcgui.DialogProgress()
            if not silence: pDialog.create('Pulsar list integration', 'Creating the .strm files')
            path = xbmc.translatePath('special://temp')
            database = shelve.open(path + 'pulsar-subscription-data.db')
            cont = 0
            directory = ''
            for cm, item in enumerate(listing):
                item = ' '.join(item.split()).replace(':', '').replace('/', '-')
                if database.has_key(item):
                    data = database[item]
                else:
                    # create the item
                    data = {}
                    if len(ID)> 0:
                        data['ID'] = ID[cm]
                        if type_list == 'SHOW':
                            tv_show = TV_Show_code(ID[cm])
                            data['first_season'] = tv_show.first_season
                            data['last_season'] = tv_show.last_season
                            data['last_episode'] = tv_show.last_episode
                    else:
                        if type_list == 'MOVIE':
                            movie = Movie(item)  # name of the movie with (year) format: Frozen (2013)
                            data['ID'] = movie.code  # search the IMDB id
                        elif type_list == 'SHOW':
                            tv_show = TV_Show(item)
                            data['ID'] = tv_show.code
                            data['first_season'] = tv_show.first_season
                            data['last_season'] = tv_show.last_season
                            data['last_episode'] = tv_show.last_episode
                    data['type'] = type_list
                    data['season'] = 0
                    data['episode'] = 0
                if type_list == 'MOVIE' and data['type'] == 'MOVIE' and data['episode'] == 0:  # add movies
                    cont += 1
                    directory = folder
                    link = 'plugin://plugin.video.pulsar/movie/%s/%s' % (data['ID'], action)
                    with open("%s%s.strm" % (directory, item), "w") as text_file:  # create .strm
                        text_file.write(link)
                    data['episode'] = 1
                    if not silence: pDialog.update(int(float(cm) / total * 100), 'Creating %s%s.strm...' % (directory, item))
                    xbmc.log('%s%s.strm added' % (directory, item), xbmc.LOGINFO)
                elif type_list == 'SHOW' and data['type'] == 'SHOW':  # add shows
                    directory = folder + item + folder[-1]
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    for season in range(max(data['season'], data['first_season']), data['last_season'] + 1):
                        for episode in range(data['episode'] + 1, data['last_episode'][season] + 1):
                            cont += 1
                            link = 'plugin://plugin.video.pulsar/show/%s/season/%s/episode/%s/%s' % (data['ID'], season, episode, action)
                            print link
                            if not silence: pDialog.update(int(float(cm) / total * 100), "%s%s S%02dE%02d.strm" % (directory, item, season, episode))
                            with open("%s%s S%02dE%02d.strm" % (directory, item, season, episode), "w") as text_file:  # create .strm
                                text_file.write(link)
                        data['episode'] = 1 # change to new season and reset the episode to 1
                    data['season'] = data['last_season']
                    data['episode'] = data['last_episode'][data['last_season']]
                    if not silence: pDialog.update(int(float(cm) / total * 100), 'Creating %s%s.strm...' % (directory, item))
                    xbmc.log('%s%s.strm added' % (directory, item), xbmc.LOGINFO)
                # update database
                database[item] = data
                database.sync()
                if not silence:
                    if pDialog.iscanceled():
                        break
            # confirmation and close database
            database.close()
            pDialog.close()
            if cont > 0:
                if not silence:
                    dialog.ok('Integration is done!!', '%s Files added. You need to update your library' % cont)
                else:
                    dialog.notification('Subscription Pulsar list', '%s Files added.' % cont, xbmcgui.NOTIFICATION_INFO, 1000)
            else:
                xbmc.log('[service.subscription] No new files')
                if not silence:
                    dialog.ok('Integration is done!!', 'Files already added.  It may you need to clear the database')
                else:
                    dialog.notification('Subscription Pulsar list', 'No New Files', xbmcgui.NOTIFICATION_INFO, 1000)
    else:
        xbmc.log('[service.subscription] Empty List')
        if not silence: dialog.ok('Empty List!!', 'Try another list number, please')