
import re, string, datetime, operator

####################################################################################################

VIDEO_PREFIX = "/video/history_canada"

NAME = L('Title')

ART             = 'art-default.jpg'
ICON            = 'icon-default.png'

HISTORY_PARAMS      = ["IX_AH1EK64oFyEbbwbGHX2Y_2A_ca8pk", "z/History%20Player%20-%20Video%20Center"]

FEED_LIST    = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=%s&startIndex=1&endIndex=500&query=hasReleases&query=CustomText|PlayerTag|%s&field=airdate&field=fullTitle&field=author&field=description&field=PID&field=thumbnailURL&field=title&contentCustomField=title&field=ID&field=parent"

FEEDS_LIST    = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=%s&startIndex=1&endIndex=500&query=categoryIDs|%s&query=BitrateEqualOrGreaterThan|400000&query=BitrateLessThan|601000&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&contentCustomField=title"

DIRECT_FEED = "http://release.theplatform.com/content.select?format=SMIL&pid=%s&UserName=Unknown&Embedded=True&TrackBrowser=True&Tracking=True&TrackLocation=True"

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('VideoTitle'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)


####################################################################################################
def MainMenu():
    
    if not Platform.HasFlash():
        return MessageContainer(NAME, L('This channel requires Flash. Please download and install Adobe Flash on the computer running Plex Media Server.'))

    dir = MediaContainer(viewGroup="List")
    
    network = HISTORY_PARAMS
    
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    showList = {}
    showCount = 0
    #items = sorted(content['items'], key=attrgetter('fullTitle'))
    items = content['items']
    #Log(items)
    items.sort(key=operator.itemgetter('fullTitle'))
    #Log(items)
    #parent = ""
    for item in items:
        if "Full Episodes" in item['fullTitle']:
            title = item['fullTitle']
            title = title.split('/')[1]
            id = item['ID']
            thumb = item['thumbnailURL']
            #dir.Append(Function(DirectoryItem(VideosPage, title, thumb=thumb), pid=network[0], id=id))
            try:
                if showList[title]:
                    discard = dir.Pop(showList[title]['index'])
                    #Log('Removed: %s' %discard.title)
                    dir.Append(Function(DirectoryItem(SeasonsPage, title), network=network))
                else:
                    pass
            except:
                #Log('showList does not contain %s' % title)
                showList[title] = {'id':id, 'index':showCount}
                showCount +=1
                dir.Append(Function(DirectoryItem(VideosPage, title), pid=network[0], id=id))
                
    dir.Sort('title')
    
    return dir
    
####################################################################################################
def VideoPlayer(sender, pid):

    videosmil = HTTP.Request(DIRECT_FEED % pid).content
    player = videosmil.split("ref src")
    player = player[2].split('"')
    #Log(player)
    if ".mp4" in player[1]:
        player = player[1].replace(".mp4", "")
        try:
            clip = player.split(";")
            clip = "mp4:" + clip[4]
        except:
            clip = player.split("/video/")
            player = player.split("/video/")[0]
            clip = "mp4:/video/" + clip[-1]
    else:
        player = player[1].replace(".flv", "")
        try:
            clip = player.split(";")
            clip = clip[4]
        except:
            clip = player.split("/video/")
            player = player.split("/video/")[0]
            clip = "/video/" + clip[-1]

    #Log(player)
    #Log(clip)
    return Redirect(RTMPVideoItem(player, clip))
    
####################################################################################################

def VideosPage(sender, pid, id):

    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList", art=sender.art)
    pageUrl = FEEDS_LIST % (pid, id)
    feeds = JSON.ObjectFromURL(pageUrl)
    #Log(feeds)

    for item in feeds['items']:
        title = item['title']
        pid = item['PID']
        summary =  item['description'].replace('In Full:', '')
        duration = item['length']
        thumb = item['thumbnailURL']
        airdate = int(item['airdate'])/1000
        subtitle = 'Originally Aired: ' + datetime.datetime.fromtimestamp(airdate).strftime('%a %b %d, %Y')
        dir.Append(Function(VideoItem(VideoPlayer, title=title, subtitle=subtitle, summary=summary, thumb=thumb, duration=duration), pid=pid))
    
    dir.Sort('title')
    
    return dir
    
####################################################################################################
            
def SeasonsPage(sender, network):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", art=sender.art)
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    #Log(sender.itemTitle)
    #Log(content)
    for item in content['items']:
        if sender.itemTitle in item['fullTitle']:
            title = item['fullTitle']
            #Log(title)
            title = title.split('/')[-1]
            #if title == 'New This Week':
            #    title = item['title']
            id = item['ID']
            #thumb = item['thumbnailURL']
            dir.Append(Function(DirectoryItem(VideosPage, title, thumb=sender.thumb), pid=network[0], id=id))
    dir.Sort('title')
    return dir
            
####################################################################################################

