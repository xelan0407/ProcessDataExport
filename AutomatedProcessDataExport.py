import asyncio
import time
from ReadWriteFiles import create_folder 
from db_api import get_Item_Records
import os

async def checkDaySwitch(lastdate_localtime):
    await asyncio.sleep(1)
    Lastdate = time.mktime(lastdate_localtime)
    actualdate = time.time()

    if actualdate > Lastdate + 86400: #letztes Datum + 1 Tag
        result = time.localtime(actualdate)
        return (result.tm_year, result.tm_mon, result.tm_mday, 0, 0, 0, result.tm_wday, result.tm_yday, result.tm_isdst)
    else:
        return lastdate_localtime

def deleteFile(filepath):
    try:
        os.remove(filepath)
        print(f"File {filepath} deleted")
    except OSError as e:
        print(e)

class SAFELASTDATE:

    def __init__(self) -> None:
        self.file = "./txt/lastdate.txt"


    def write(self, lastdate : float):
        data =""
        for item in lastdate:
            data = data + str(item) + ","
        data = data[:-1]
        f = open(self.file, "w")
        f.write(data)
        f.close()

        return True

    def read(self):
        result = []
        f = open(self.file, "r")
        data = f.read()
        f.close()
        data = data.split(",")

        for item in data:
            result.append(int(item))
            
        return tuple(result)

    def exists(self):
        try:
            f = open(self.file, "x")
            return "new file"
        except Exception as e:
            return "file already exists"

        





def main():
    safelastdate = SAFELASTDATE()
    create_folder("./txt")

    if safelastdate.exists() == "file already exists":
        lastdate = safelastdate.read()
        
    else:
        lastdate = (1970, 1, 1, 1, 0, 0, 3, 1, 0)
        safelastdate.write(lastdate=lastdate)
    while (True):
        newdate = asyncio.run(checkDaySwitch(lastdate))
        print(time.mktime(newdate))
        if newdate != lastdate:

            
            #Dies ist der Ort um die Datenbank auszulesen und 
            #die enstsprechenden daten zwischen den Zeitstempeln zu exportieren
            get_Item_Records(starttimestamp=lastdate, endtimestamp=newdate)
            deleteFile("C:/ProgramData/WebIQ/WebIQ Projects/spoolreport-server-beta/spool.id")
            safelastdate.write(lastdate= newdate)
            lastdate = newdate
        print(f"{time.time()}: läuft noch")
        


main()

