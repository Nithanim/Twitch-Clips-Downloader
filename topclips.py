import requests, os, argparse
from slugify import slugify
from time import sleep

def MarkDone(slug):
    with open("done.txt", "a+") as myfile:
        myfile.write("{}\n".format(slug))

def AlreadyDownloaded(slug):
    with open('done.txt') as myfile:
        if slug in myfile.read():
            return True
    return False

def GetClipUrl(slug):
    data = [{"operationName":"VideoAccessToken_Clip","variables":{"slug":slug},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"9bfcc0177bffc730bd5a5a89005869d2773480cf1738c592143b5173634b7d15"}}}]
    r = requests.post("https://gql.twitch.tv/gql", headers={"Client-Id": "kimne78kx3ncx6brgo4mv6wki5h1ko"}, json=data)
    try:
        return r.json()[0]['data']['clip']['videoQualities'][0]['sourceURL']
    except:
        print("[ERROR] Could not fetch clip URL")
        return None

def DownloadClip(download_path, slug, filename, i):
    if not AlreadyDownloaded(slug):
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c=='-' or c==' ']).rstrip()
        filename = u"{}-{}.mp4".format(str(i), filename)
        clip_url = GetClipUrl(slug)
        if clip_url != None:
            r = requests.get(clip_url)
            with open(u"{}/{}".format(download_path, filename), 'wb') as f:
                f.write(r.content)
            print(u"[SUCCESS] Saved as {}".format(filename))
            MarkDone(slug)
    else:
        print("[SKIPPED] Already downloaded this file ({})".format(filename))

# Create the parser
my_parser = argparse.ArgumentParser(description='Downloads your Twitch clips')

# Add the arguments
my_parser.add_argument('Username', metavar='username', type=str, help='Twitch channel you want to download clips from')
my_parser.add_argument('--limit', required=False)

# Execute the parse_args() method
args = my_parser.parse_args()

Twitch_Username = args.Username
if args.limit != None:
    Clips_Limit = int(args.limit)
else:
    Clips_Limit = None
try:
    os.mkdir("./top-clips")
    print("[SUCCESS] Directory top-clips Created ") 
except FileExistsError:
    print("[INFO] Directory top-clips already exists")
try:
    os.mkdir("./top-clips/{}".format(Twitch_Username))
    print("[SUCCESS] Directory top-clips/{} Created ".format(Twitch_Username)) 
except FileExistsError:
    print("[INFO] Directory top-clips/{} already exists".format(Twitch_Username))

i = 1
cursor = None
nextPage = True
doneParsing = False
MarkDone("")
Range_List = ["ALL_TIME"]
if Clips_Limit == None:
    Range_List = ["LAST_DAY", "LAST_WEEK", "LAST_MONTH", "ALL_TIME"]

for Range in Range_List:
    while not doneParsing:
        data = [{"operationName":"ClipsCards__User","variables":{"login":Twitch_Username,"limit":20, "cursor": cursor, "criteria":{"filter":Range}},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"b73ad2bfaecfd30a9e6c28fada15bd97032c83ec77a0440766a56fe0bd632777"}}}]
        r = requests.post("https://gql.twitch.tv/gql", headers={"Client-Id": "kimne78kx3ncx6brgo4mv6wki5h1ko"}, json=data)
        if "errors" not in r.json()[0]:
            nextPage = r.json()[0]['data']['user']['clips']['pageInfo']['hasNextPage']
            clips = r.json()[0]['data']['user']['clips']['edges']
            for clip in clips:
                if Clips_Limit != None:
                    if i <= Clips_Limit:
                        DownloadClip("./top-clips/{}".format(Twitch_Username), clip['node']['slug'], u"{} - {} - {}".format(str(clip['node']['viewCount']), clip['node']['createdAt'].split('T')[0], clip['node']['title']), i)
                        i = i + 1
                    else:
                        doneParsing = True
                else:
                    DownloadClip("./top-clips/{}".format(Twitch_Username), clip['node']['slug'], u"{} - {} - {}".format(str(clip['node']['viewCount']), clip['node']['createdAt'].split('T')[0], clip['node']['title']), i)
                    i = i + 1
            if not r.json()[0]['data']['user']['clips']['pageInfo']['hasNextPage']:
                doneParsing = True
            cursor = clips[len(clips) - 1]['cursor']
            if doneParsing:
                print("[SUCCESS] Fetched {} clips from {}".format(int(i - 1), Range))
        else:
            if r.json()[0]['errors'][0]['message'] == "service timeout":
                print("[TIMEOUT] Received rate-limit, waiting 5 seconds...")
                sleep(5)
    doneParsing = False
if len(Range_List) > 1:
    print("[SUCCESS] Reached clips limit, maximum amount of clips retrieved")
else:
    print("[SUCCESS] Finished fetching clips")
