# -*- coding: utf_8 -*-
import hashlib
from BeautifulSoup import BeautifulSoup
import httplib
import os
import pickle
import re
import traceback
import urllib
import shelve
import tempfile
import htmlentitydefs
from htmlentitydefs import name2codepoint as n2cp


"""
A list of the implemented webservices (from what.cd )
=====================================

# User

    * user.getUserId
    * user.getInfo
    * user.getUserStats
    * user.getUserPercentile
    * user.getUserCommunity
    * user.getTorrentsSeedingByUser
    * user.getTorrentsSnatchedByUser
    * user.getTorrentsUploadedByUser

    * user.getUserJoinedDate
    * user.getUserLastSeen
    * user.getUserDataUploaded
    * user.getUserDataDownloaded
    * user.getUserRatio
    * user.getUserRequiredRatio

    * user.getUserUploadedPercentile
    * user.getUserDownloadedPercentile
    * user.getUserUploadedPercentile
    * user.getUserTorrentsUploadedPercentile
    * user.getUserFilledRequestPercentile
    * user.getUserBountySpentPercentile
    * user.getUserPostsMadePercentile
    * user.getUserArtistsAddedPercentile
    * user.getUserOverallRankPercentile

    * user.getUserCommunityForumPosts
    * user.getUserCommunityTorrentsComments
    * user.getUserCommunityStartedCollages
    * user.getUserCommunityContributedCollages
    * user.getUserCommunityRequestsFilled
    * user.getUserCommunityRequestsVoted
    * user.getUserCommunityTorrentsUploaded
    * user.getUserCommunityUniqueGroups
    * user.getUserCommunityPerfectFlacs
    * user.getUserCommunityTorrentsSeeding
    * user.getUserCommunityTorrentsLeeching
    * user.getUserCommunityTorrentsSnatched
    * user.getUserCommunityInvited
    * user.getUserCommunityArtistsAdded


# Artist

    * artist.getArtistReleases
    * artist.getArtistImage
    * artist.getArtistInfo
    * artist.getArtistTags
    * artist.getArtistSimilar
    * artist.getArtistRequests


# Torrent

    * torrent.getTorrentParentId
    * torrent.getTorrentDownloadURL
    * torrent.getTorrentDetails
    * torrent.getTorrentSize
    * torrent.getTorrentSnatched
    * torrent.getTorrentSeeders
    * torrent.getTorrentLeechers
    * torrent.getTorrentUploadedBy
    * torrent.getTorrentFolderName
    * torrent.getTorrentFileList
    * torrent.getTorrentDescription


# Authenticate

    * authenticate.getAuthenticatedUserId
    * authenticate.getAuthenticatedUserAuthCode
    * authenticate.getAuthenticatedUserDownload
    * authenticate.getAuthenticatedUserRatio
    * authenticate.getAuthenticatedUserRequiredRatio

"""
class ResponseBody:
	pass

class WhatBase(object):
    """An abstract webservices object."""
    whatcd = None

    def __init__(self, whatcd):
        self.whatcd = whatcd
        #authenticate user
        if Authenticate(self.whatcd).isAuthenticated() is False:
            self.whatcd.headers = Authenticate(self.whatcd).getAuthenticatedHeader()

    def _request(self,type, path, data, headers):
        return Request(self.whatcd,type,path,data,headers)

    def _parser(self):
        return Parser(self.whatcd)

    def utils(self):
        return Utils()


class Utils():

    def md5(self, text):
        """Returns the md5 hash of a string."""

        h = hashlib.md5()
        h.update(self._string(text))

        return h.hexdigest()

    def _unicode(self, text):
        if type(text) == unicode:
            return text

        if type(text) == int:
            return unicode(text)

        return unicode(text, "utf-8")

    def _string(self, text):
        if type(text) == str:
            return text

        if type(text) == int:
            return str(text)

        return text.encode("utf-8")

    def _number(self,string):
        """
            Extracts an int from a string. Returns a 0 if None or an empty string was passed
        """

        if not string:
            return 0
        elif string == "":
            return 0
        else:
            try:
                return int(string)
            except ValueError:
                return float(string)

    def substituteEntity(self, match):
        ent = match.group(2)
        if match.group(1) == "#":
            return unichr(int(ent))
        else:
            cp = n2cp.get(ent)

            if cp:
                return unichr(cp)
            else:
                return match.group()

    def decodeHTMLEntities(self, string):
        entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")
        return entity_re.subn(self.substituteEntity, string)[0]
    

    def unescapeHTMLEntity(self,string):
        mapping = htmlentitydefs.name2codepoint
        for key in mapping:
            string = string.replace("&%s;" %key, unichr(mapping[key]))

        return self.decodeHTMLEntities(string)
    
    def escape(self, html):
        """Returns the given HTML with ampersands, quotes and carets encoded."""
        return html.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"').replace('&#39;',"'").replace('&deg','°')

class WhatCD(object):

	def __init__(self, username, password, site, loginpage, headers, authenticateduserinfo):
            # This singleton class owns the singleton parser and utils
            self.parser = Parser(self)
            self.utils = Utils()
            self.proxy_enabled = False
            self.cache_backend = None
            #credentials
            self.username = username
            self.password = password
            self.site = site
            self.loginpage = loginpage
            self.headers = headers
            self.authenticateduserinfo = authenticateduserinfo

        def getCredentials(self):
            """
                Returns an authenticated user credentials object
            """
            self.authenticateduserinfo['retrieve'] = True
            return Authenticate(self)

        def getUser(self, username):
            """
                Returns an user object
            """
            return User(username, self)

        def getTorrent(self, id):
            """
                Returns a torrent object
            """
            return Torrent(id, self)

        def getArtist(self, name):
            """
                Returns an artist object
            """
            return Artist(name, self)

        def enableProxy(self, host, port):
            """Enable a default web proxy"""
            self.proxy = [host, self.utils._number(port)]
            self.proxy_enabled = True

        def disableProxy(self):
            """Disable using the web proxy"""

            self.proxy_enabled = False

        def isProxyEnabled(self):
            """Returns True if a web proxy is enabled."""
            return self.proxy_enabled

        def getProxy(self):
            """Returns proxy details."""
            return self.proxy

        def enableCaching(self, file_path = None):
            """Enables caching request-wide for all cachable calls.
            * file_path: A file path for the backend storage file. If
            None set, a temp file would probably be created, according the backend.
            """
            if not file_path:
                file_path = tempfile.mktemp(prefix="whatapi_tmp_")

            self.cache_backend = _ShelfCacheBackend(file_path)

        def disableCatching(self):
            """Disables all caching features."""

            self.cache_backend = None

        def isCatchingEnabled(self):
            """Returns True if caching is enabled."""

            return not (self.cache_backend == None)

        def getCacheBackend(self):

            return self.cache_backend

def getWhatcdNetwork(username = "", password = ""):
    """
    Returns a preconfigured WhatCD object for what.cd

    authenticated user: user logged in what.cd
    username: a username of a valid what.cd user
    password: user's password
    headers: default headers

    """

    return WhatCD (
                    username = username,
                    password = password,
                    site = "what.cd",
                    loginpage = "/login.php",
                    headers = {
                        "Content-type": "application/x-www-form-urlencoded",
                        'Accept-Charset': 'utf-8',
                        'User-Agent': "whatapi"
                        },
                    authenticateduserinfo = {
                        "id": None,
                        "authcode":"None",
                        "upload":0,
                        "downloaded":0,
                        "ratio":0,
                        "required":0,
                        "retrieve":False
                    })



class _ShelfCacheBackend(object):
    """Used as a backend for caching cacheable requests."""
    def __init__(self, file_path = None):
        self.shelf = shelve.open(file_path)

    def getHTML(self, key):
        return self.shelf[key]

    def setHTML(self, key, xml_string):
        self.shelf[key] = xml_string

    def hasKey(self, key):
        return key in self.shelf.keys()
    

class Request(object):
    """web service operation."""

    def __init__(self, whatcd,type, path, data, headers):

        self.whatcd = whatcd
        self.utils = Utils()
        self.type = type
        self.path = path
        self.data = data
        self.headers = headers
        if whatcd.isCatchingEnabled():
            self.cache = whatcd.getCacheBackend()

    def getCacheKey(self):
        """The cache key is a md5 hash of request params."""

        key = self.type + self.path + self.data
        return Utils().md5(key)

    def getCachedResponse(self):
        """Returns a file object of the cached response."""

        if not self.isCached():
            response = self.downloadResponse()
            self.cache.setHTML(self.getCacheKey(), response)
        return self.cache.getHTML(self.getCacheKey())

    def isCached(self):
        """Returns True if the request is already in cache."""

        return self.cache.hasKey(self.getCacheKey())

    def downloadResponse(self):
        print "downloading from what.cd"
        conn = httplib.HTTPConnection(self.whatcd.site)
        rb = ResponseBody()
        
        if self.whatcd.isProxyEnabled():
            conn = httplib.HTTPConnection(host = self.whatcd.getProxy()[0], port = self.whatcd.getProxy()[1])
            conn.request(method = self.type, url="http://" + self.whatcd.site + self.path, body = self.data, headers = self.headers)
        else:
            conn.request(self.type, self.path, self.data, self.headers)

        response = conn.getresponse()
        rb.headers = response.getheaders()
        # Rip all inline JavaScript out of the response in case it hasn't been properly escaped
        rb.body = re.sub('<script type="text/javascript">[^<]+</script>', '', response.read())
        conn.close()
        return rb

    def execute(self, cacheable = False):
        """Returns the HTML DOM response of the Request from the server"""
        if self.whatcd.isCatchingEnabled() and cacheable:
            response = self.getCachedResponse()
        else:
            response = self.downloadResponse()

        return response

class Authenticate(WhatBase):

    def __init__(self, whatcd):

        self.whatcd = whatcd
        self.parser = Parser(whatcd)
        #if not loged in what.cd, do it
        if self.isAuthenticated() is False:
            self.whatcd.headers = self.getAuthenticatedHeader()

    def getAuthenticatedHeader(self):
        """
            Log user in what.cd and returns the authenticated header
        """
        if os.path.exists("cookie"):
            f = open("cookie", "r")
            self.whatcd.headers = pickle.load(f)
        else:
            print "creating cookie"
            f = open('cookie', 'w')
            headers = self._request("GET", self.whatcd.loginpage, "", self.whatcd.headers).execute(True).headers
            cookie=dict(headers)['set-cookie']
            web_session=re.search("web_session=[a-f0-9]+", cookie).group(0)
            headers = { "Cookie": web_session, "Content-Type": "application/x-www-form-urlencoded"}

            loginform= {'username': self.whatcd.username, 'password': self.whatcd.password \
                    , 'keeplogged': '1', 'login': 'Login'}
            data = urllib.urlencode(loginform)
            headers = self._request("POST", self.whatcd.loginpage, data, headers).execute(True).headers
            try:
                cookie=dict(headers)['set-cookie']
                session=re.search("session=[^;]+", cookie).group(0)
                self.whatcd.headers = { "Cookie": web_session + "; " + session }
                pickle.dump(self.whatcd.headers, f)
            except (KeyError, AttributeError):
                # Login failed, most likely bad creds or the site is down, nothing to do
                print "login failed"
                self.whatcd.headers = None
        f.close()

        #If credentials requested, get user authenticated user info
        if self.whatcd.authenticateduserinfo["retrieve"]:
            self.whatcd.authenticateduserinfo = self.getAuthenticatedUserInfo()

        return self.whatcd.headers

    def getAuthenticatedUserInfo(self):
        """
            Returns authenticated user's info
        """
        homepage = BeautifulSoup(self._request("GET", "/index.php", "", self.whatcd.headers).execute(True).body)
        authuserinfo = self.parser.authenticatedUserInfo(homepage.find("div", {"id": "userinfo"}))
        return authuserinfo


    def isAuthenticated(self):
        """
            Checks if user is authenticated
        """
        if "Cookie" in self.whatcd.headers:
            return True
        else:
            return False

    def getAuthenticatedUserId(self):
        """
            Returns authenticated user's id
        """
        return self.whatcd.authenticateduserinfo["id"]

    def getAuthenticatedUserAuthCode(self):
        """
            Returns authenticated user's authcode
        """
        return self.whatcd.authenticateduserinfo["authcode"]


    def getAuthenticatedUserUpload(self):
        """
            Returns authenticated user's total uploaded data
        """
        return self.whatcd.authenticateduserinfo["uploaded"]


    def getAuthenticatedUserDownload(self):
        """
            Returns authenticated user's total downloaded data
        """
        return self.whatcd.authenticateduserinfo["downloaded"]


    def getAuthenticatedUserRatio(self):
        """
            Returns authenticated user's ratio
        """
        return self.whatcd.authenticateduserinfo["ratio"]

    def getAuthenticatedUserRequiredRatio(self):
        """
            Returns authenticated user's required ratio
        """
        return self.whatcd.authenticateduserinfo["required"]


class User(WhatBase):
    """A What.CD user"""

    def __init__(self, username, whatcd):
        """Create an user object.
        # Parameters:
            * name str: The user's name.
        """
        WhatBase.__init__(self, whatcd)
        self.name = username
        self.whatcd = whatcd
        self.userpage = "/user.php?"
        self.userid = None
        self.userinfo = self.getInfo()

    def getUserName(self):
        """
            Returns user's name
        """
        return self.username

    def getUserId(self):
        """
            Returns user's id, None if user doesn't exists
        """
        if self.userid:
            return self.userid
        else:
            idform = {'action': "search", 'search': self.name}
            data = urllib.urlencode(idform)
            headers = self._request("GET", self.userpage + data, "", self.whatcd.headers).execute(True).headers
            if dict(headers) is None:
                return None
            else:
                self.userid = dict(headers)['location'][12:]
                return self.userid

    def getInfo(self):
        """
            Returns user's info if paranoia level is set to 0
        """
        if self.getUserId():
            form = {'id': self.getUserId()}
            data = urllib.urlencode(form)
            userpage = BeautifulSoup(self._request("GET", self.userpage + data, "", self.whatcd.headers).execute(True).body)
            return self._parser().userInfo(userpage.find("div", {"class": "sidebar"}), self.name)
        else:
            return None
            print "no user id retrieved"

    def getUserStats(self):
        """
            Returns a dictionnary with user's general stats
        """
        return self.userinfo['stats']

    def getUserPercentile(self):
        """
            Returns a dictionnary with user's percentile stats
        """
        return self.userinfo['percentile']

    def getUserCommunity(self):
        """
            Returns a dictionnary with user's community stats
        """
        return self.userinfo['community']

    def getTorrentsSeedingByUser(self,page=1):
        """
            Returns a list with all user's seeding music torrents
            in form of dictionary {page(tuple with current and total),tag, dlurl, id, artist, album}
        """
        url = "/"+self.getUserCommunityTorrentsSeeding()[1]+"&page=%d"%page
        torrentspage = BeautifulSoup(self._request("GET", url, "", self.whatcd.headers).execute(True).body)
        return self._parser().torrentsList(torrentspage)

    def getTorrentsSnatchedByUser(self,page=1):
        """
            Returns a list with all user's snatched music torrents
            in form of dictionary {page(tuple with current and total),tag, dlurl, id, artist, album}
        """
        url = "/"+self.getUserCommunityTorrentsSnatched()[1]+"&page=%d"%page
        torrentspage = BeautifulSoup(self._request("GET", url, "", self.whatcd.headers).execute(True).body)
        return self._parser().torrentsList(torrentspage)

    def getTorrentsUploadedByUser(self,page=1):
        """
            Returns a list with all user's uploaded music torrents
            in form of dictionary {page(tuple with current and total),tag, dlurl, id, artist, album}
        """
        url = "/"+self.getUserCommunityTorrentsUploaded()[1]+"&page=%d"%page
        torrentspage = BeautifulSoup(self._request("GET", url, "", self.whatcd.headers).execute(True).body)
        return self._parser().torrentsList(torrentspage)



    ###############################################
    #              specific values                #
    ###############################################

    ######## stats ###########

    def getUserJoinedDate(self):
        """
            Returns user's joined date
        """
        return self.userinfo['stats']['joined']

    def getUserLastSeen(self):
        """
            Returns user's last seen date
        """
        return self.userinfo['stats']['lastseen']

    def getUserDataUploaded(self):
        """
            Returns user's uploaded data amount
        """
        return self.userinfo['stats']['uploaded']

    def getUserDataDownloaded(self):
        """
            Returns user's downloaded data amount
        """
        return self.userinfo['stats']['downloaded']

    def getUserRatio(self):
        """
            Returns user's ratio
        """
        return self.userinfo['stats']['ratio']

    def getUserRequiredRatio(self):
        """
            Returns user's required ratio
        """
        return self.userinfo['stats']['rratio']

    ######## percentile ###########

    def getUserUploadedPercentile(self):
        """
            Returns user's uploaded percentile
        """
        return self.userinfo['percentile']['dataup']

    def getUserDownloadedPercentile(self):
        """
            Returns user's uploaded percentile
        """
        return self.userinfo['percentile']['datadown']

    def getUserTorrentsUploadedPercentile(self):
        """
            Returns user's torrents uploaded percentile
        """
        return self.userinfo['percentile']['torrentsup']

    def getUserFilledRequestPercentile(self):
        """
            Returns user's filled requests percentile
        """
        return self.userinfo['percentile']['reqfilled']

    def getUserBountySpentPercentile(self):
        """
            Returns user's bounty spent percentile
        """
        return self.userinfo['percentile']['bountyspent']

    def getUserPostsMadePercentile(self):
        """
            Returns user's posts made percentile
        """
        return self.userinfo['percentile']['postsmade']

    def getUserArtistsAddedPercentile(self):
        """
            Returns user's artists added percentile
        """
        return self.userinfo['percentile']['artistsadded']

    def getUserOverallRankPercentile(self):
        """
            Returns user's overall ranking percentile
        """
        return self.userinfo['percentile']['overall']

    ######## community ###########

    def getUserCommunityForumPosts(self):
        """
            Returns a tuple with user's total forum posts and its relative url
        """
        return self.userinfo['community']['forumposts']

    def getUserCommunityTorrentsComments(self):
        """
            Returns a tuple with user's total torrents comments and its relative url
        """
        return self.userinfo['community']['torrentscomments']

    def getUserCommunityStartedCollages(self):
        """
            Returns a tuple with user's total started collages and its relative url
        """
        return self.userinfo['community']['startedcollages']

    def getUserCommunityContributedCollages(self):
        """
            Returns a tuple with user's total contributed collages and its relative url
        """
        return self.userinfo['community']['contributedcollages']

    def getUserCommunityRequestsFilled(self):
        """
            Returns a tuple with user's total requests filled and its relative url
        """
        return self.userinfo['community']['reqfilled']

    def getUserCommunityRequestsVoted(self):
        """
            Returns a tuple with user's total requests voted and its relative url
        """
        return self.userinfo['community']['reqvoted']

    def getUserCommunityTorrentsUploaded(self):
        """
            Returns a tuple with user's total torrents uploaded and its relative url
        """
        return self.userinfo['community']['uploaded']

    def getUserCommunityUniqueGroups(self):
        """
            Returns a tuple with user's total unique groups and its relative url
        """
        return self.userinfo['community']['uniquegroups']

    def getUserCommunityPerfectFlacs(self):
        """
            Returns a tuple with user's total perfect FLACS and its relative url
        """
        return self.userinfo['community']['pefectflacs']

    def getUserCommunityTorrentsSeeding(self):
        """
            Returns a tuple with user's total torrents seeding and its relative url
        """
        return self.userinfo['community']['seeding']

    def getUserCommunityTorrentsLeeching(self):
        """
            Returns a tuple with user's total torrents leeching and its relative url
        """
        return self.userinfo['community']['leeching']

    def getUserCommunityTorrentsSnatched(self):
        """
            Returns a tuple with user's total torrents snatched and its relative url
        """
        return self.userinfo['community']['snatched']

    def getUserCommunityInvited(self):
        """
            Returns user's total of invites
        """
        return self.userinfo['community']['invited'][0]

    def getUserCommunityArtistsAdded(self):
        """
            Returns user's total of artists added
        """
        return self.userinfo['community']['artists']

class Torrent(WhatBase):
    """A What.CD torrent"""

    def __init__(self, id, whatcd):
        """Create a torrent object.
        # Parameters:
            * id str: The torrent's id.
        """
        WhatBase.__init__(self, whatcd)
        self.id = id
        self.whatcd = whatcd
        self.torrentspage = "/torrents.php?"
        self.torrentinfo = self.getInfo()

    def getTorrentUrl(self):
        """
            Returns a dictionnary torrent's real URL
        """
        form = {'torrentid': self.id}
        data = urllib.urlencode(form)
        headers = self._request("GET", self.torrentspage + data, "", self.whatcd.headers).execute(True).headers
        if dict(headers) is None:
            return None
        else:
            return dict(headers)['location']

    def getInfo(self):
        """
            Returns a dictionnary with torrents's info
        """
        if self.getTorrentUrl():
            torrentpage = BeautifulSoup(self._request("GET", "/"+self.getTorrentUrl(), "", self.whatcd.headers).execute(True).body)
            return self._parser().torrentInfo(torrentpage, self.id)
        else:
            return None
            print "no user id retrieved"


    def getTorrentParentId(self):
        """
            Returns torrent's group id
        """
        return self.torrentinfo['torrent']['parentid']

    def getTorrentDownloadURL(self):
        """
            Returns relative url to download the torrent
        """
        return self.torrentinfo['torrent']['downloadurl']

    def getTorrentDetails(self):
        """
            Returns torrent's details (format / bitrate / media)
        """
        return self.torrentinfo['torrent']['details']

    def getTorrentSize(self):
        """
            Returns torrent's size
        """
        return self.torrentinfo['torrent']['size']


    def getTorrentSnatched(self):
        """
            Returns torrent's total snatches
        """
        return self.torrentinfo['torrent']['snatched']


    def getTorrentSeeders(self):
        """
            Returns torrent's current seeders
        """
        return self.torrentinfo['torrent']['seeders']

    def getTorrentLeechers(self):
        """
            Returns torrent's current leechers
        """
        return self.torrentinfo['torrent']['leechers']

    def getTorrentUploadedBy(self):
        """
            Returns torrent's uploader
        """
        return self.torrentinfo['torrent']['uploadedby']

    def getTorrentFolderName(self):
        """
            Returns torrent's folder name
        """
        return self.torrentinfo['torrent']['foldername']

    def getTorrentFileList(self):
        """
            Returns torrent's file list
        """
        return self.torrentinfo['torrent']['filelist']


    def getTorrentDescription(self):
        """
            Returns torrent's description / empty string is there's none
        """
        return self.torrentinfo['torrent']['torrentdescription']


class Artist(WhatBase):
    """A What.CD artist"""

    def __init__(self, name, whatcd):
        """Create an artist object.
        # Parameters:
            * name str: The artist's name.
        """
        WhatBase.__init__(self, whatcd)
        self.name = name
        self.whatcd = whatcd
        self.artistpage = "/artist.php?"
        self.info = self.getInfo()


    def getArtistName(self):
        """
            Returns artist's name
        """
        return self.name

    def getArtistId(self):
        """
            Returns artist's id, None if artist's not found
        """
        form = {'artistname': self.name}
        data = urllib.urlencode(form)
        headers = self._request("GET", self.artistpage + data, "", self.whatcd.headers).execute(True).headers
        if dict(headers)['location'][0:14] != 'artist.php?id=':
            return None
        else:
            return dict(headers)['location'][14:]

    def getInfo(self):
        """
            Returns user's info if paranoia level is set to 0
        """
        if self.getArtistId():
            form = {'id': self.getArtistId()}
            data = urllib.urlencode(form)
            artistpage = BeautifulSoup(self._request("GET", self.artistpage + data, "", self.whatcd.headers).execute(True).body)
            return self._parser().artistInfo(artistpage)
        else:
            return None
            print "no artist info retrieved"

    def getArtistReleases(self):
        """
            Returns a list with all artist's releases in form of dictionary {releasetype, year, name, id}
        """
        return self.info['releases']

    def getArtistImage(self):
        """
            Return the artist image URL, None if there's no image
        """
        return self.info['image']

    def getArtistInfo(self):
        """
            Return the artist's info, blank string if none
        """
        return self.info['info']

    def getArtistTags(self):
        """
            Return a list with artist's tags
        """
        return self.info['tags']

    def getArtistSimilar(self):
        """
            Return a list with artist's similar artists
        """
        return self.info['similarartists']

    def getArtistRequests(self):
        """
            Returns a list with all artist's requests in form of dictionary {requestname, id}
        """
        return self.info['requests']

    def setArtistInfo(self, artist, info):
        creds = self.whatcd.getCredentials()
        print "authenticated user auth code:"
        print creds.getAuthenticatedUserInfo()['authcode']



class Parser(object):

        def __init__(self,whatcd):
            self.utils = Utils()
            self.whatcd = whatcd
            self.utils = Utils()

	def handleExpatError(self, description, response, debugfile, messagecallback = None):
            self.debugMessage(description, messagecallback)
            self.debugMessage(traceback.format_exc(), messagecallback)

            # Dump the search response for debug purposes
            try:
                self.debugMessage("Creating HTML dump for debug in file %s" % debugfile, messagecallback)
                dumpfile = open(debugfile, "w")
                dumpfile.write(response)
                dumpfile.close()
            except (IOError):
                self.debugMessage("IO Error creating debug file", messagecallback)
                self.debugMessage(traceback.format_exc(), messagecallback)

	def authenticatedUserInfo(self, dom):
            """
                Parse the index page and returns a dictionnary with basic authenticated user information
            """
            userInfo = {}
            soup = BeautifulSoup(str(dom))
            for ul in soup.fetch('ul'):
                if ul["id"] == "userinfo_username":
                    #retrieve user logged id
                    hrefid = ul.findAll('li')[0].find("a")["href"]
                    regid = re.compile('[0-9]+')
                    if regid.search(hrefid) is None:
                        self.debugMessage("not found  href to retrieve user id")
                    else:
                        userInfo["id"] = regid.search(hrefid).group(0)

                    #retrieve user logged id
                    hrefauth = ul.findAll('li')[2].find("a")["href"]
                    regauth = re.compile('=[0-9a-fA-F]+')
                    if regid.search(hrefid) is None:
                        self.debugMessage("not found  href to retrieve user id")
                    else:
                        userInfo["authcode"] = regauth.search(hrefauth).group(0)[1:]

                elif ul["id"] == "userinfo_stats":
                    if len(ul.findAll('li')) > 0:
                        userInfo["uploaded"] = ul.findAll('li')[0].find("span").string
                        userInfo["downloaded"] = ul.findAll('li')[1].find("span").string
                        userInfo["ratio"] = ul.findAll('li')[2].findAll("span")[1].string
                        userInfo["required"] = ul.findAll('li')[3].find("span").string
                        userInfo["authenticate"] = True

            return userInfo

	def userInfo(self, dom, user):
            """
                Parse an user's page and returns a dictionnary with its information
            """
            userInfo = {'stats':{}, 'percentile':{}, 'community':{}}
            soup = BeautifulSoup(str(dom))

            for div in soup.fetch('div',{'class':'box'}):
                if div.findAll('div')[0].string == "Personal":
                    if div.find('ul').findAll('li')[1].string != "Paranoia Level: 0":
                        break
                        return 0

            userInfo['stats']['joined'] = soup.findAll('li')[0].find('span')['title']
            userInfo['stats']['lastseen'] = soup.findAll('li')[1].find('span')['title']
            userInfo['stats']['uploaded'] = soup.findAll('li')[2].string[10:]
            userInfo['stats']['downloaded'] = soup.findAll('li')[3].string[12:]
            userInfo['stats']['ratio'] = soup.findAll('li')[4].find('span').string
            userInfo['stats']['rratio'] = soup.findAll('li')[5].string[16:]
            userInfo['percentile']['dataup'] = soup.findAll('li')[6].string[15:]
            userInfo['percentile']['datadown'] = soup.findAll('li')[7].string[17:]
            userInfo['percentile']['torrentsup'] = soup.findAll('li')[8].string[19:]
            userInfo['percentile']['reqfilled'] = soup.findAll('li')[9].string[17:]
            userInfo['percentile']['bountyspent'] = soup.findAll('li')[10].string[14:]
            userInfo['percentile']['postsmade'] = soup.findAll('li')[11].string[12:]
            userInfo['percentile']['artistsadded'] = soup.findAll('li')[12].string[15:]
            userInfo['percentile']['overall'] = soup.findAll('li')[13].find('strong').string[14:]
            '''community section. Returns a tuple (stats,url)
            if user == authenticated user, sum 2 to array position to skip email and passkey <li>s
            shown in personal information'''
            if user == self.whatcd.username:i = 2
            else:i = 0
            userInfo['community']['forumposts'] = (soup.findAll('li')[16+i].contents[0].string[13:len(soup.findAll('li')[16+i].contents[0].string)-2],\
                                                        soup.findAll('li')[16+i].find('a')['href'])
            userInfo['community']['torrentscomments'] = (soup.findAll('li')[17+i].contents[0].string[18:len(soup.findAll('li')[17+i].contents[0].string)-2],\
                                                        soup.findAll('li')[17+i].find('a')['href'])
            userInfo['community']['startedcollages'] = (soup.findAll('li')[18+i].contents[0].string[18:len(soup.findAll('li')[18+i].contents[0].string)-2],\
                                                        soup.findAll('li')[18+i].find('a')['href'])
            userInfo['community']['contributedcollages'] = (soup.findAll('li')[19+i].contents[0].string[25:len(soup.findAll('li')[19+i].contents[0].string)-2],\
                                                        soup.findAll('li')[19+i].find('a')['href'])
            userInfo['community']['reqfilled'] = (soup.findAll('li')[20+i].contents[0].string[17:len(soup.findAll('li')[20+i].contents[0].string)-2],\
                                                        soup.findAll('li')[20+i].find('a')['href'])
            userInfo['community']['reqvoted'] = (soup.findAll('li')[21+i].contents[0].string[16:len(soup.findAll('li')[21+i].contents[0].string)-2],\
                                                        soup.findAll('li')[21+i].find('a')['href'])
            userInfo['community']['uploaded'] = (soup.findAll('li')[22+i].contents[0].string[10:len(soup.findAll('li')[22+i].contents[0].string)-2],\
                                                        soup.findAll('li')[22+i].find('a')['href'])
            userInfo['community']['uniquegroups'] = (soup.findAll('li')[23+i].contents[0].string[15:len(soup.findAll('li')[23+i].contents[0].string)-2],\
                                                        soup.findAll('li')[23+i].find('a')['href'])
            userInfo['community']['pefectflacs'] = (soup.findAll('li')[24+i].contents[0].string[16:len(soup.findAll('li')[24+i].contents[0].string)-2],\
                                                        soup.findAll('li')[24+i].find('a')['href'])
            userInfo['community']['seeding'] = (soup.findAll('li')[25+i].contents[0].string[9:len(soup.findAll('li')[25+i].contents[0].string)-2],\
                                                        soup.findAll('li')[25+i].find('a')['href'])
            userInfo['community']['leeching'] = (soup.findAll('li')[26+i].contents[0].string[10:len(soup.findAll('li')[26+i].contents[0].string)-2],\
                                                        soup.findAll('li')[26+i].find('a')['href'])
            #NB: there's a carriage return and white spaces inside the snatched li tag
            userInfo['community']['snatched'] = (soup.findAll('li')[27+i].contents[0].string[10:len(soup.findAll('li')[27+i].contents[0].string)-7],\
                                                        soup.findAll('li')[27+i].find('a')['href'])
            userInfo['community']['invited'] = (soup.findAll('li')[28+i].contents[0].string[9:],\
                                                        None)
            userInfo['community']['artists'] = soup.findAll('li')[12]['title']

            return userInfo

        def torrentInfo(self, dom, id):
            """
                Parse a torrent's page and returns a dictionnary with its information
            """
            torrentInfo = {'torrent':{}}
            torrentfiles = []
            torrentdescription = ""
            soup = BeautifulSoup(str(dom))
            groupidurl = soup.findAll('div', {'class':'linkbox'})[0].find('a')['href']
            torrentInfo['torrent']['parentid'] = groupidurl[groupidurl.rfind("=")+1:]
            torrentInfo['torrent']['downloadurl'] = soup.findAll('tr',{'id':'torrent%s'%id})[0].findAll('a',{'title':'Download'})[0]['href']
            torrentInfo['torrent']['details'] = soup.findAll('tr',{'id':'torrent%s'%id})[0].findAll('a')[-1].string[8:]
            torrentInfo['torrent']['size'] = soup.findAll('tr',{'id':'torrent%s'%id})[0].findAll('td')[1].string
            torrentInfo['torrent']['snatched'] = soup.findAll('tr',{'id':'torrent%s'%id})[0].findAll('td')[2].string
            torrentInfo['torrent']['seeders'] = soup.findAll('tr',{'id':'torrent%s'%id})[0].findAll('td')[3].string
            torrentInfo['torrent']['leechers'] = soup.findAll('tr',{'id':'torrent%s'%id})[0].findAll('td')[4].string
            torrentInfo['torrent']['uploadedby'] = soup.findAll('tr',{'id':'torrent_%s'%id})[0].findAll('a')[0].string
            foldername = soup.findAll('div',{'id':'files_%s'%id})[0].findAll('div')[1].string
            torrentInfo['torrent']['foldername'] = self.utils.decodeHTMLEntities(foldername)
            files = soup.findAll('div',{'id':'files_%s'%id})[0].findAll('tr')
            for file in files[1:-1]:
                torrentfiles.append(self.utils.decodeHTMLEntities(file.contents[0].string))
            torrentInfo['torrent']['filelist'] = torrentfiles
            #is there any description?
            if len(soup.findAll('tr',{'id':'torrent_%s'%id})[0].findAll('blockquote')) > 1:
                description = torrentInfo['torrent']['description'] = soup.findAll('tr',{'id':'torrent_%s'%id})[0].findAll('blockquote')[1].contents
                for content in description:
                    if content.string:
                        info = "%s%s" % (info, self.utils._string(content.string))
                        torrentdescription = "%s%s" % (torrentdescription, self.utils._string(content.string))
            torrentInfo['torrent']['torrentdescription'] = torrentdescription

            return torrentInfo

        def artistInfo(self, dom):
            """
                Parse an artist's page and returns a dictionnary with its information
            """
            artistInfo = {}
            releases = []
            requests = []
            infoartist = ""
            tagsartist = []
            similarartists = []
            soup = BeautifulSoup(str(dom))
            for releasetype in soup.fetch('table',{'class':'torrent_table'}):
                releasetypenames = releasetype.findAll('strong')
                releasetypename = releasetype.findAll('strong')[0].string
                for release in releasetypenames[1:-1]:
                    #skip release edition info and Freeleech! <strong>s
                    if len(release.parent.contents) > 1 and len(release.contents) > 1 :
                        releaseyear = release.contents[0][0:4]
                        releasename = release.contents[1].string
                        releasehref = release.contents[1]['href']
                        releaseid = releasehref[releasehref.rfind('=')+1:]
                        releases.append({'releasetype':releasetypename,\
                         'year': releaseyear,'name':self.utils.decodeHTMLEntities(releasename),'id':releaseid})

            artistInfo['releases'] = releases
            #is there an artist image?
            artistInfo['image'] = None
            if soup.find('div', {'class':'box'}).find('img'):
                artistInfo['image'] = soup.find('div', {'class':'box'}).find('img')['src']
            #is there any artist info?
            contents = soup.find('div', {'class':'body'}).contents
            if len(contents) > 0:
                for content in contents:
                    if content.string:
                        infoartist = "%s%s" % (infoartist, self.utils._string(content.string))
            artistInfo['info'] = self.utils.decodeHTMLEntities(infoartist)
            #is there any artist tags?
            if soup.findAll('ul',{'class':'stats nobullet'})[0].findAll('li'):
                ul = soup.findAll('ul',{'class':'stats nobullet'})[0].findAll('li')
                for li in ul:
                    if li.contents[0].string:
                        tagsartist.append(self.utils._string(li.contents[0].string))
            artistInfo['tags'] = tagsartist
            #is there any similar artist?
            if soup.findAll('ul',{'class':'stats nobullet'})[2].findAll('span',{'title':'2'}):
                artists = soup.findAll('ul',{'class':'stats nobullet'})[2].findAll('span',{'title':'2'})
                for artist in artists:
                    if artist.contents[0].string:
                        similarartists.append(self.utils._string(artist.contents[0].string))
            artistInfo['similarartists'] = similarartists
            #is there any request?
            if soup.find('table',{'id':'requests'}):
                for request in soup.find('table',{'id':'requests'}).findAll('tr',{'class':re.compile('row')}):
                    requests.append({'requestname':request.findAll('a')[1].string,'id':request.findAll('a')[1]['href'][28:]})

            artistInfo['requests'] = requests

            return artistInfo

        def torrentsList(self,dom):
            """
                Parse a torrent's list page and returns a dictionnary with its information
            """
            torrentslist = []
            torrentssoup = dom.find("table", {"width": "100%"})
            pages = 0
            #if there's at least 1 torrent in the list
            if torrentssoup:
                navsoup = dom.find("div", {"class": "linkbox"})
                #is there a page navigation bar?
                if navsoup.contents:
                    #there's more than 1 page of torrents
                    lastpage = navsoup.contents[-1]['href']
                    pages = lastpage[18:lastpage.find('&')]
                else:
                    #there's only one page
                    pages = 1
                #fetch all tr except first one (column head)
                for torrent in torrentssoup.fetch('tr')[1:-1]:
                    #exclude non music torrents
                    if torrent.find('td').find('div')['class'][0:10] == 'cats_music':
                        #workaround to check artist field content
                        if len(torrent.findAll('td')[1].find('span').parent.contents) == 11:
                            #one artist
                            torrentartist = torrent.findAll('td')[1].find('span').nextSibling.nextSibling.string
                            torrentalbum = torrent.findAll('td')[1].find('span').nextSibling.nextSibling.nextSibling.nextSibling.string
                        elif len(torrent.findAll('td')[1].find('span').parent.contents) == 9:
                            #various artists
                            torrentartist = 'Various Artists'
                            torrentalbum = torrent.findAll('td')[1].find('span').nextSibling.nextSibling.string
                        elif len(torrent.findAll('td')[1].find('span').parent.contents) == 13:
                            #two artists
                            torrentartist = torrent.findAll('td')[1].find('span').nextSibling.nextSibling.string + " and " \
                                + torrent.findAll('td')[1].find('span').nextSibling.nextSibling.nextSibling.nextSibling.string
                            torrentalbum = torrent.findAll('td')[1].find('span').nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.string
                        torrenttag = torrent.find('td').contents[1]['title']
                        torrentdl = torrent.findAll('td')[1].find('span').findAll('a')[0]['href']
                        torrentrm = torrent.findAll('td')[1].find('span').findAll('a')[1]['href']
                        torrentid = torrentrm[torrentrm.rfind('=')+1:]
                        torrentslist.append({'tag':torrenttag,'dlurl':torrentdl,'id':torrentid, \
                                            'artist':self.utils.decodeHTMLEntities(torrentartist),\
                                            'album':self.utils.decodeHTMLEntities(torrentalbum),'pages':pages})

            return torrentslist



if __name__ == "__main__":
	print "Module to manage what.cd as a web service"
