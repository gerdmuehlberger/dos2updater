import os
import json
import shutil
from distutils.dir_util import copy_tree
from os import listdir
from os.path import isfile, join
from pathlib import Path
import ftplib

with open('config/secrets.json', 'r') as configfile:
    config=configfile.read()

secrets = json.loads(config)
host = secrets['host']
user = secrets['user']
password = secrets['password']


print("Copying latest gamefiles to local transfer folder...\n")

gamefilespath = secrets['filepath']
latestgamefiles = str(sorted(Path(gamefilespath).iterdir(), key=os.path.getmtime, reverse=True)[0])
gamefilefoldername = os.path.basename(os.path.normpath(latestgamefiles))


try:
    os.mkdir(f'./{gamefilefoldername}')
except:
    print(f"local gamefilefolder {gamefilefoldername} already exists.\n")
copy_tree(latestgamefiles, f'./{gamefilefoldername}' )

gamefiles = []
for f in os.listdir(f'./{gamefilefoldername}'):
    gamefiles.append(f)

print("Establishing FTP Connection...")
try:
    ftp = ftplib.FTP(host)
    ftp.login(user, password)
    print("Success!\n")
except Exception as e:
    print(f"Could not connect to FTP server {e}")

files = ftp.nlst()
ftpgamefiledirectoryname = ''

for f in files:
    if "QuickSave" in f:
        ftpgamefiledirectoryname = f
    else:
        pass


#pull from ftp
print("Backing up gamefiles...\n")
try:
    ftp.cwd(ftpgamefiledirectoryname)
    ftpgamefiles = ftp.nlst()

    for f in ftpgamefiles:
        try:
            ftp.retrbinary("RETR " + f, open(f, 'wb').write)
        except:
            pass

    try:
        list = [f for f in listdir('.') if isfile(join('.', f))]
        for f in list:
            if "QuickSave" in f:
                shutil.move(f, 'backups-ftp')
            else:
                pass
    except Exception as e:
        print(e)

except:
    print("No QuickSave folder to backup available on ftp server!\n")


print("Deleting current gamefiles on ftp server...\n")
#after pulling as a backup delete current file on server
try:
    for f in ftpgamefiles:
        try:
            ftp.delete(f)
        except:
            pass

    ftp.cwd('/')
    ftp.rmd(ftpgamefiledirectoryname)

except:
    print("No QuickSave folder to delete available!\n")


# push to ftp
print("Pushing new gamefiles to ftp server...\n")

ftp.mkd(gamefilefoldername)
ftp.cwd(gamefilefoldername)

for f in gamefiles:
    with open(gamefilefoldername + '/' + f, "rb") as file:
        # use FTP's STOR command to upload the file
        ftp.storbinary(f"STOR {f}", file)


ftp.quit()

shutil.rmtree(f'./{gamefilefoldername}')
print("Done! Gamefiles on ftp server updated.")
