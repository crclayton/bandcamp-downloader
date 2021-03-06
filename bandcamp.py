#!/usr/bin/python

# Bandcamp MP3 Downloader
# Copyright (c) 2012-2015 cisoun
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Note : this is a procedural code. I don't know why some people really want
# to turn it OOP. It has one job and it does it right like this.
# Please don't blame or whip me.
#
#
# Contributors:
#    JamieMellway
#    jtripper
#    diogovk
#    haansn08
#    crclayton

VERSION = "0.2.2"


import json
import math
import os
import re
import shutil
import sys
import urllib.request
from urllib import error
from datetime import datetime, date, time
try:
    import stagger
    from stagger.id3 import *
    can_tag = True
except:
    print("[Error] Can't import stagger, will skip mp3 tagging.")
    can_tag = False


# Download a file and show its progress.
# Taken from http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def Download(url, destination, message):
    # Check if the file is availabe otherwise, skip.
    if not re.match("^(https?:)?//(\w+)\.(\w+)\.([\w\?\/\=\-\&\.])*$", str(url)):
        return(False)
    # Let's do this !
    try:
        # Check if protocol was given. Otherwise, add it.
        if not url.startswith("http"):
            url = "http:" + url
        u = urllib.request.urlopen(url)
    except URLError: # Does it work ?
        print(u.getcode())
    file = open(destination, "wb")
    meta = u.info()
    file_size = int(meta["Content-Length"])
    file_size_dl = 0
    block_sz = 8192
    t = message + " (" + "{:d}".format(int(file_size / 1024)) + " ko) : "
    pb_len = 25
    space_len = 80 - pb_len - len(t) - 2
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        file.write(buffer)
        progress = math.ceil(file_size_dl * pb_len / file_size)
        status =  t + (" " * space_len) + "[" + ("#" * progress) + (" " * (pb_len - progress)) + "]"
        status = status + chr(8) * (len(status))
        sys.stdout.write(status)
        sys.stdout.flush()
    file.close()
    print()
    return(True)

# Return some JSON things...
def GetDataFromProperty(p, bracket = False):
    try:
        if bracket:
            return(json.loads("[{" + (re.findall(p + "[ ]?: \[?\{(.+)\}\]?,", s, re.MULTILINE)[0] + "}]")))
        return(re.findall(p + "[ ]?: ([^,]+)", s, re.DOTALL)[0])
    except:
        return(0)

# Print a JSON data.
def PrintData(d):
    print(json.dumps(d, sort_keys = True, indent = 2))


if __name__ == "__main__":
#===============================================================================
#
#    0. Welcome.
#
#===============================================================================


    print("=" * 80)
    print("\n\tBandcamp MP3 Downloader " + VERSION)
    print("\t----")
    print("\tRemember, piracy isn't good for the artists,")
    print("\tuse this script carefully, buy their albums and support them !\n")
    print("=" * 80)
    
#===============================================================================
#
#    1. Let's get the bandcamp url in the parameters.
#
#===============================================================================
    save_directory = os.getcwd()

    # parameters given?
    if len(sys.argv) == 1:
        print("Please, pass a URL or filename at the end of the command !")
        print("e.g: " + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah\n")
        print("     " + sys.argv[0] + " -f urls.txt")
        sys.exit(0)

    # passing a file with a list of urls?
    if sys.argv[1] == "-f" or sys.argv[1] == "--file":
        filename = sys.argv[2]
        if not os.path.isfile(filename):
            print("[Error] This file doesn't exist")
            sys.exit(0)

        with open(filename) as f: 
            album_list = f.readlines()
    else:
        album_list = [sys.argv[1]]

    for album_url in album_list:

        if album_url.isspace(): continue
        print("Downloading: " + album_url)

        # Valid URL ?
        if not re.match("^https?://(\w+)\.bandcamp\.com([-\w]|/)*$", album_url):
            print("[Error] This url doesn't seem to be a valid Bandcamp url.")
            print("\nIt should look something like this :\n" + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah\n")
            if input("Look for albums anyway ? [y/n] : ") != "y": sys.exit(0)
            print()

    #===============================================================================
    #
    #    2. Find some informations.
    #
    #===============================================================================


        # Load the web page.
        try:
            content = urllib.request.urlopen(album_url)
            s = content.read().decode("utf-8")
            content.close()
        except:
            print("[Error] Can't reach the page.")
            print("Aborting...")
            sys.exit(0)

        # We only load the essential datas.
        tracks = GetDataFromProperty("trackinfo", True)
        if tracks == 0 :
            print("[Error] Tracks not found. It is unecessary to continue.")
            print("Aborting...")
            sys.exit(0)
        album = GetDataFromProperty("current", True)[0]
        artist = GetDataFromProperty("artist").replace('"', "").replace("\\", "")
        artwork = GetDataFromProperty("artThumbURL").replace('"', "").replace("\\", "")
        artwork_full = GetDataFromProperty("artFullsizeUrl").replace('"', "").replace("\\", "")
        directory = ""
        if album == 0 :
            print("[Warning] Album informations not found.")
        elif "title" in album:
            directory = re.sub("[^A-Za-z0-9-_ ]+", "", album["title"])
            os.makedirs(directory, exist_ok=True)
            os.chdir(directory)
        if artist == 0 : print("[Warning] Artist informations not found.")
        if artwork == 0  : print("[Warning] Cover not found.")
        if artwork_full == 0  : print("[Warning] Full size cover not found.")
        try:
            release_date = datetime.strptime(album["release_date"], "%d %b %Y %H:%M:%S GMT")
        except:
            print("[Warning] Cannot find release date.")


    #===============================================================================
    #
    #    3. Download tracks & tag.
    #
    #===============================================================================


        # List the tracks.
        print("\nTracks found :\n----")
        for i in range(0, len(tracks)):
            # Track number available ?
            track_num = str(tracks[i]["track_num"]) + ". " if tracks[i]["track_num"] != None else ""
            print(track_num + str(tracks[i]["title"].encode(sys.stdout.encoding, errors="replace")))
        exit

        # Artwork.
        print()
        artwork_name = "cover-mini.jpg" #artwork.split('/')[-1]
        artwork_full_name = "cover.jpg" #artwork_full.split('/')[-1]
        #Download(artwork, artwork_name, "Cover") # Let's skip the mini cover for a while.
        Download(artwork_full, artwork_full_name, "Fullsize cover")

        # Download tracks.
        print()
        got_error = False
        for track in tracks:
            # Skip track number if missing.
            if track["track_num"] != None:
                f = "%02d. %s.mp3" % (track["track_num"], track["title"].replace("\\", "").replace("/", ""))
            else:
                f = "%s.mp3" % track["title"].replace("\\", "").replace("/", "")
            # Skip if file unavailable. Can happens with some albums.
            message = "Track " + str(tracks.index(track) + 1) + "/" + str(len(tracks))
            try:
                print(track)
                downloaded = Download(track["file"]["mp3-128"], f, message)
                if not downloaded:
                    raise Exception
            except Exception:
                got_error = True
                print(message + " : File unavailable. Skipping...")
                continue

            # Tag.
            if can_tag == False : continue # Skip the tagging operation if stagger cannot be loaded.
            # Try to load the mp3 in stagger.
            try:
                t = stagger.read_tag(f)
            except:
                # Try to add an empty ID3 header.
                # As long stagger crashes when there's no header, use this hack.
                # ID3v2 infos : http://id3.org/id3v2-00
                m = open(f, "r+b")
                old = m.read()
                m.seek(0)
                m.write(b"\x49\x44\x33\x02\x00\x00\x00\x00\x00\x00" + old) # Meh...
                m.close
            # Let's try again...
            try:
                t = stagger.read_tag(f)
                t.album = album["title"]
                t.artist = artist
                if release_date.strftime("%H:%M:%S") == "00:00:00":
                    t.date = release_date.strftime("%Y-%m-%d")
                else:
                    t.date = release_date.strftime("%Y-%m-%d %H:%M:%S")
                t.title = track["title"]
                t.track = track["track_num"]
                t.picture = artwork_full_name
                t.write()
            except:
                print("[Warning] Can't add tags, skipped.")

        if got_error:
            print()
            print(80 * "=")
            print("OOPS !")
            print("Looks like some tracks haven't been reached.")
            print("It can happen with some albums. They sometimes don't allow to listen to some of")
            print("their tracks. Sorry for you.")
            print(80 * "=")
            # Remove directory if given.
            # if directory != "":
            #     os.chdir("..")
            #     shutil.rmtree(directory)


    #===============================================================================
    #
    #    4. Add album's informations.
    #
    #===============================================================================


        print("\nAdding additional infos...")
        file = open("INFOS", "w+")
        file.write("Artist : " + artist)
        if album["title"] != None : file.write("\nAlbum : " + album["title"])
        if release_date != None : file.write("\nRelease date : " + release_date.strftime("%Y-%m-%d %H:%M:%S"))
        if album["credits"] != None : file.write("\n\nCredits :\n----\n" + album["credits"])
        if album["about"] != None : file.write("\n\nAbout :\n----\n" + album["about"])
        file.close()

        os.chdir(save_directory) 
        print("\nAlbum downloaded !\n")

    # Done.
    print("\nFinished !\n")
