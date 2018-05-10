#whatapi

A python module to manage what.cd / redacted.ch as a web service


A list of the implemented webservices (from what.cd / redacted.ch )
=====================================

# User

    * user.getUserId
    * user.getInfo

    * user.getTorrentsSeeding
    * user.getTorrentsSnatched
    * user.getTorrentsUploaded

    * user.specificUserInfo

        # Atributes:

        ######## stats ###########
        -joindate
        -lastseen
        -dataup
        -datadown
        -ratio
        -rratio

        ######## percentile ###########

        -uppercentile
        -downpercentile
        -torrentsuppercentile
        -reqfilledpercentile
        -bountyspentpercentile
        -postsmadepercentile
        -artistsaddedpercentile
        -overallpercentile

        ######## community ###########

        -postsmade
        -torrentscomments
        -collagesstarted
        -collagescontr
        -reqfilled
        -reqvoted
        -uploaded
        -unique
        -perfect
        -seeding
        -leeching
        -snatched
        -invited
        -artistsadded


# Artist

    * artist.getArtistReleases
    * artist.getArtistImage
    * artist.getArtistInfo
    * artist.getArtistTags
    * artist.getArtistSimilar
    * artist.getArtistRequests

    + artist.setArtistInfo


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
    * torrent.isTorrentFreeLeech
    * torrent.isTorrentReported
    * torrent.getTorrentReleaseType


# Authenticate

    * authenticate.getAuthenticatedUserId
    * authenticate.getAuthenticatedUserAuthCode
    * authenticate.getAuthenticatedUserDownload
    * authenticate.getAuthenticatedUserUpload()
    * authenticate.getAuthenticatedUserRatio
    * authenticate.getAuthenticatedUserRequiredRatio


Getting started:

<pre>
import whatapi


# you need to authenticate yourself
username = "your_what.cd_user_name"
password = "your_what.cd_password"

whatcd = whatapi.getWhatcdNetwork(username, password)

# now you can use that object every where
whatcd.enableCaching()
whatuser = whatcd.getUser("devilcius")
torrents_snatched = whatuser.getTorrentsSnatched(page)
</pre>
