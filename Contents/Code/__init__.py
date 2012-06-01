TITLE = "History.ca"
ART = 'art-default.jpg'
ICON = 'icon-default.png'
HISTORY_PARAMS = ["IX_AH1EK64oFyEbbwbGHX2Y_2A_ca8pk", "z/History%20Player%20-%20Video%20Center"]
FEED_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=%s&startIndex=1&endIndex=500&query=hasReleases&query=CustomText|PlayerTag|%s&field=airdate&field=fullTitle&field=author&field=description&field=PID&field=thumbnailURL&field=title&contentCustomField=title&field=ID&field=parent"
FEEDS_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=%s&startIndex=1&endIndex=500&query=categoryIDs|%s&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&contentCustomField=title&contentCustomField=Episode&contentCustomField=Season"
DIRECT_FEED = "http://release.theplatform.com/content.select?format=SMIL&pid=%s&UserName=Unknown&Embedded=True&TrackBrowser=True&Tracking=True&TrackLocation=True"
LOADCATS = { 
	'full':['Full Episodes']
	}
RE_SEASON_TEST=Regex("S([0-9]+)$")

####################################################################################################

def Start():
	Plugin.AddPrefixHandler("/video/history_canada", MainMenu, TITLE, ICON, ART)

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

	# Setup the default attributes for the ObjectContainer
	ObjectContainer.title1 = TITLE
	ObjectContainer.view_group = 'List'
	ObjectContainer.art = R(ART)
	
	# Setup the default attributes for the other objects
	DirectoryObject.thumb = R(ICON)
	DirectoryObject.art = R(ART)
	EpisodeObject.thumb = R(ICON)
	EpisodeObject.art = R(ART)

	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def MainMenu():
	
	return LoadShowList(cats='full')


####################################################################################################
def LoadShowList(cats):
	oc = ObjectContainer()
	
	shows_with_seasons = {}
	shows_without_seasons = {}

	network = HISTORY_PARAMS
	content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
	
	for item in content['items']:
		if WantedCats(item['title'],cats):
			title = item['fullTitle'].split('/')[1]
			thumb_url = item['thumbnailURL']
			iid = item['ID']

			if RE_SEASON_TEST.search(item['title']):
				
				if not(title in shows_with_seasons):
					shows_with_seasons[title] = ""
					oc.add(
						DirectoryObject(
							key = Callback(SeasonsPage, cats=cats, network=network, showtitle=title),
							title = title, 
							thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
						)
					)
			else:
				if not(title in shows_without_seasons):
					shows_without_seasons[title] = ""
					oc.add(
						DirectoryObject(
							key = Callback(VideosPage, pid=network[0], iid=iid),
							title = title,
							thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
						)
					)

	# sort here
	oc.objects.sort(key = lambda obj: obj.title)

	return oc


####################################################################################################
def VideoParse(pid):

	videosmil = HTTP.Request(DIRECT_FEED % pid).content
	Log(videosmil)
	player = videosmil.split("ref src")
	player = player[2].split('"')
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

	return Redirect(RTMPVideoItem(player, clip))

####################################################################################################

def VideosPage(pid, iid):

	oc = ObjectContainer(
		view_group="InfoList"
	)
	
	pageUrl = FEEDS_LIST % (pid, iid)
	feeds = JSON.ObjectFromURL(pageUrl)
	Log(feeds)

	for item in feeds['items']:
		title = item['title']
		pid = item['PID']
		summary =  item['description'].replace('In Full:', '')
		duration = item['length']
		thumb_url = item['thumbnailURL']
		airdate = int(item['airdate'])/1000
		originally_available_at = Datetime.FromTimestamp(airdate).date()

		try:
			# try to set the seasons and episode info
			# NB: episode is set with 'index' (not in framework docs)!
			season = item['contentCustomData'][1]['value']
			seasonint = int(float(season))
			episode = item['contentCustomData'][0]['value']
			episodeint = int(float(episode))

			oc.add(
				EpisodeObject(
					key = Callback(VideoParse, pid=pid),
					rating_key = pid, 
					title = title,
					summary=summary,
					duration=duration,
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON),
					originally_available_at = originally_available_at,
	 				season = seasonint,
	 				index = episodeint
				)
			)

		except:
			# if we don't get the season/episode info then don't set it
			oc.add(
				EpisodeObject(
					key = Callback(VideoParse, pid=pid),
					rating_key = pid, 
					title = title,
					summary=summary,
					duration=duration,
					thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON),
					originally_available_at = originally_available_at
				)
			)

	return oc
	
####################################################################################################

def SeasonsPage(cats, network, showtitle):
	oc = ObjectContainer(
		view_group="List"
	)
	content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
	#Log(content)
	
	for item in content['items']:
		if showtitle in item['parent']:
			title = item['fullTitle'].split('/')[-1]
			iid = item['ID']
			thumb_url = item['thumbnailURL']
			Log('Gerk: fullTitle: %s',item['fullTitle'])
			# Let's remove 'Full Episodes' from the default title
			# and change S# into Season # where applicable
			if ('Full Episodes' in item['fullTitle']):
				try:
					title = "Season " + RE_SEASON_TEST.search(item['title']).group(1)
				except:
					title = title
			else:
				try:
					title = "Season " + RE_SEASON_TEST.search(item['title']).group(1) + " - " + title.split('-')[0] 
				except:
					title = title

			oc.add(
				DirectoryObject(
					key = Callback(VideosPage, pid=network[0], iid=iid),
					title = title,
					thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
				)
			)

	oc.objects.sort(key = lambda obj: obj.title)

	return oc
	
####################################################################################################
def WantedCats(thisShow,cats):
	
	for show in LOADCATS[cats]:
		if show in thisShow:
			return 1				
	return 0
