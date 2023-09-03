#!/usr/bin/python3

import os
import json
import configparser
from pickle import FALSE, TRUE
import sys
import sqlite3
import subprocess
import pipes

connection = sqlite3.connect("videos_metadata.db")
cursor = connection.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS videos(id INTEGER PRIMARY KEY AUTOINCREMENT, identifier, title, extension, encodings_name, encodings_resolution)")

if not len(sys.argv) > 1:
    print("Usage: pass config ini file as first parameter, you can force metadata rescan by setting second parameter to true (false by default)\neg.\npython3 generateJson.py config.ini\npython3 generateJson.py config.ini true")
    quit()

configFile = sys.argv[1]

if not os.path.isfile(configFile):
    print("Passed ini file do not exist")
    quit()

if not len(sys.argv) > 2:
    force_ffprobe = FALSE
elif sys.argv[2] == "true":
    force_ffprobe = TRUE
else:
    force_ffprobe = FALSE


config = configparser.ConfigParser()
config.read(configFile)

out_files = {"Library": {"name": "Library", "list": []}}

for (root, dirs, files) in os.walk(config['videos']['videos_relative_path'], followlinks=True):
    for dir in dirs:
        directory = (os.path.join(root, dir))
        dumpDir = directory.replace(
            config['videos']['videos_relative_path'] + "/", "")
        out_files[dumpDir] = {"name": dumpDir, "list": []}
    for file in sorted(files, key=str.casefold):
        title = ""
        extension = ""
        if ".mp4" in file[-4:] or ".mkv" in file[-4:]:
            ok = TRUE
            title = file[:-4]
            extension = file[-4:]
        else:
            ok = FALSE

        if ok == TRUE:

            fullfile = (os.path.join(root, file))

            encodings_name = ""
            encodings_resolution = ""
            result = cursor.execute(
                "SELECT encodings_name, encodings_resolution FROM videos WHERE identifier = :identifier AND title = :title AND extension = :extension", {
                    "identifier": config['videos']['identifier'],
                    "title": title,
                    "extension": extension,
                })
            row = result.fetchone()
            if row is None:
                cmd = [
                    "ffprobe -v quiet -print_format json -show_format -show_streams " + pipes.quote(fullfile)]
                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                metadataJson = result.stdout
                d = json.loads(metadataJson)
                streams = d.get("streams", [])
                for stream in streams:
                    if "codec_type" in stream:
                        if stream["codec_type"] == "video":
                            encodings_name = stream["codec_name"]
                            encodings_resolution = stream["height"]
                            cursor.execute("insert into videos(identifier, title, extension, encodings_name, encodings_resolution) values (?, ?, ?, ?, ?)", (
                                config['videos']['identifier'], title, extension, encodings_name, encodings_resolution))
                            connection.commit()
            else:
                encodings_name = row[0]
                encodings_resolution = row[1]

            entry = fullfile.replace(
                config['videos']['videos_relative_path'], "")
            expected_img = config['videos']['videos_relative_path'] + \
                "/"+config['videos']['thumbnails_folder']+entry+".jpg"
            img = "http://"+config['videos']['ip'] + "/" + config['videos']['videos_url_folder'] + expected_img.replace(
                config['videos']['videos_relative_path'], "") if os.path.isfile(expected_img) else ""

            subDir = fullfile.replace(
                config['videos']['videos_relative_path'] + "/", "")
            subDir = subDir.replace("/" + file, "")

            if not subDir in out_files:
                subDir = "Library"

            stereoModeTestTitle = title
            screenType = "flat"
            if config['videos']['sbs'] == "true":
                if "_360" in title[-4:]:
                    screenType = "sphere"
                    stereoModeTestTitle = title[:-4]
                elif "_mkx200" in title[-7:]:
                    screenType = "mkx200"
                    stereoModeTestTitle = title[:-7]
                elif "_rf52" in title[-5:]:
                    screenType = "rf52"
                    stereoModeTestTitle = title[:-5]
                elif "_fisheye" in title[-8:]:
                    screenType = "fisheye"
                    stereoModeTestTitle = title[:-8]
                elif "_fisheye" in title[-8:]:
                    screenType = "fisheye"
                    stereoModeTestTitle = title[:-8]
                elif "_screen" in title[-7:]:
                    screenType = "flat"
                else:
                    screenType = "dome"

            stereoMode = "off"
            if config['videos']['sbs'] == "true":
                if "_TB" in stereoModeTestTitle[-3:]:
                    stereoMode = "tb"
                elif "_SBS" in stereoModeTestTitle[-4:]:
                    stereoMode = "sbs"
                elif "_screen" in stereoModeTestTitle[-7:]:
                    stereoMode = "off"
                else:
                    stereoMode = "sbs"

            out_files[subDir]["list"].append(
                {"title": title,
                 "thumbnailUrl": img,
                 "is3d": "true" if config['videos']['sbs'] == "true" else "false",
                 "stereoMode": stereoMode,
                 "screenType": screenType,
                 "encodings": [
                     {
                         "name": encodings_name,
                         "videoSources": [
                             {
                                 "resolution": encodings_resolution,
                                 "url": "http://"+config['videos']['ip'] + "/" + config['videos']['videos_url_folder'] + fullfile.replace(config['videos']['videos_relative_path'], "")
                             }
                         ]
                     }
                 ]
                 })

cursor.close()
out_json = []
for entry in out_files:
    if len(out_files[entry]["list"]) > 0:
        out_json.append(out_files[entry])

print(json.dumps({'scenes': out_json}))
