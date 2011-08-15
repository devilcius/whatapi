#! /usr/bin/python
import whatapi


__author__="marcos"
__date__ ="$Aug 15, 2011 9:20:06 PM$"

if __name__ == "__main__":
    page = 1
    what = whatapi.getWhatcdNetwork('devilcius', '11por11son121')
    whatuser = what.getUser('devilcius')
    userid = whatuser.getUserId()
    torrents_snatched = whatuser.getTorrentsSnatchedByUserId(userid,page)

    for torrent in torrents_snatched:
        print torrent['year']
