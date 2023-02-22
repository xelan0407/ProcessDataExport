
from os import sep
from unicodedata import decimal
from ReadWriteFiles import create_folder, write_json, read_json 
import sqlitecommands as db
from pydantic import BaseModel
import time
import pandas as pd

class ConfigBaseModel(BaseModel):
    projektname: str
    projekt_path : str
    csv_path :str
    csv_seperator :str
    csv_decimal :str

def read(path :str):
    result = []
    f = open(path, "r")
    data = f.read()
    f.close()
    data = data.split(",")

    for item in data:
        result.append(item)
        
    return tuple(result)


def get_project_info():
    
    """
    öffne config file und gebe die darin befindlichen daten als dict zurück. (Prjektname und Pfad)
    """


    data : ConfigBaseModel
    path = "./json"
    filename = "/config.json"

    data = read_json(path = path + filename)

    return data


def get_all_projected_RecordItems():

    """
    Connects to the HMI Projektdatabase to read the projected Recorder Items and Databases and exports them dict
    :projektname: Name of the HMI Projekt For Example "2858_V1"
    :return: a Lsit of all data
    """

    #Ablauf: 
    # 1. Auslesen der Config Json für Projektpfad, Csv Pfad und Projektname um damit die notwendigen Verzeichnisse zu generieren
    # 2. Auslesen aller Projektierten Items aus der Projektdatenbank (projekt.sqlite)

    projektinfo = get_project_info()

    filename = "/project.sqlite"
    path = projektinfo["project_path"]


    try:
        conn = db.create_connection(path+filename)
        

            # create a database connection
        with conn:
            result = db.simple_select_all(conn, "_TrendItems", "*")

        return result

    except:
        print("Fehler biem lesen")
        return [[2,"wrong path or projectname", "please check config file"]]


def get_Item_Records(starttimestamp : tuple, endtimestamp : tuple): #optionale Parameter = 01.01.1970 und 19.01.2038 damit zwischen min und max für den Unix timestamp
    """
    lese die aufgenommenen Werte für ein Item aus. Standardmäßig alltime. Optional können Zeitstempel der Abfrage beigefügt werden. Dann erfolgt die Abfrage nur zwischen beiden Zeitstempeln.
    """


    #Ablauf: 
    # 1. Auslesen der Config Json für Projektpfad, Csv Pfad und Projektname um damit die notwendigen Verzeichnisse zu generieren
    # 2. Auslesen aller Projektierten Items aus der Projektdatenbank (projekt.sqlite)
    # 3. Überprüfen ob ein Item aus den Projetierten Items gleich dem über User iNterface angeforderten wert ist. Wenn nein abruch
    # 4. Mekren der datenbank in welcher das Item geloggt wird (DatabaseID=Item[2])
    # 5. Abfrage in der Item Database (DatabaseID) welche ItemID das gewünschte Item hat
    # 6. Abrufen aller geloggten Werte des Items zwischen Start und Endzeitpunkt
    # 7. Schreiben der aufegenommenen Werte in eine Json im Pfad csv


    starttimestamp = time.mktime(starttimestamp) *10000000  #da Smart HMI Zeitstempel in Nanosekunden
    endtimestamp = time.mktime(endtimestamp) * 10000000
    projektinfo = get_project_info()
    all_items = get_all_projected_RecordItems()
    records_all_items =  {}
    unit_dict = {1: "m", 2: "N" , 3: "s", 4: "rpm", 5: "A", 6: "V", 7: "W", 8: "Nm", 9: "m/s²", 10: "m/min", 11: "°C", 12: "bar", 13: "%", 14: "kg/h", 15: "kV", 16: "Hz", 17: "m/(min*s)", 18: "mm", 19: "cm", 20: ""}
    #hier datei öffnen um Konfiguration der zu exportierenden Items zu laden
    item_list = read("./txt/item_list.txt")
    project_path = projektinfo["project_path"]
    project_db_name = "/project.sqlite"
    csv_path = projektinfo["csv_path"]+"/"+"Exports"

    seperator = projektinfo["csv_seperator"]
    dec = projektinfo["csv_decimal"]
    export_json:str = projektinfo["export_json"]
    export_csv:str = projektinfo["export_csv"]

    folder_created = create_folder(path=projektinfo["csv_path"])

    for item_info in item_list:

        for Item in all_items:

            if Item[1] == item_info:

                # Einheit auslesen
                conn = db.create_connection(project_path+project_db_name) 
                with conn:
                    unit = db.select(conn= conn, tablename="_ItemListAll", SelectRowName="Unit", WhereRowName="Alias", alias= item_info)
                    unit = str(unit[0][0])

                    if unit.isdigit():
                        unit = unit_dict[int(unit)]

                    else:
                        unit = unit

                # Signifikant digits auslesen 
                    significant_digits = db.select(conn= conn, tablename="_ItemListAll", SelectRowName="Digits", WhereRowName="Alias", alias= item_info)
                    significant_digits = int(significant_digits[0][0])       
                #an der Stelle 1 steht der Alias des Items [0] = ID [2]= verwendete Datenbank 
                itemalias = Item[1]
                DatabaseID = Item[2]

                Itemdatabase = f"{project_path}/{DatabaseID}.sqlite" 
                
                #Verbindung aufbauen
                conn1 = db.create_connection(Itemdatabase)
                    
                with conn1:
                    cur = conn1.cursor()
                    #Recorder Daten für das einzelne Item
                    cur.execute(f"SELECT recorder_item_id FROM _RecorderItems WHERE item_alias =? ",(itemalias,)) #ID des Items auslesen
                    recorderItemID = cur.fetchall()
                    argument_list = (recorderItemID[0][0], starttimestamp, endtimestamp)
                    cur.execute(f"SELECT * FROM _RecorderData WHERE recorder_item_id =? AND timestamp >=? AND timestamp <=?", argument_list) #Werte für das Item auslesen
                    # Fetching all the records from the database.
                    records_item= cur.fetchall()
                    records_one_item = {}
                    for date in records_item:
                        
                        timestamp = time.localtime((date[0]/10000000))
                        # Creating a string with the format `HH:MM:SS`
                        key = f"{str(timestamp.tm_hour)}:{str(timestamp.tm_min)}:{str(timestamp.tm_sec)}"

                        #Wenn in der Visu Runden für das Item aktiv ist auf selbe anzahl Kommastellen runden
                        if significant_digits >= 0 and isinstance(date[2], float):
                            date= {key: str(round(number = float(date[2]), ndigits= significant_digits))}
                        #Ansonsten direkt in das dict    
                        else:
                            date= {key: date[2]}

                        records_one_item.update(date)
                    records_all_items.update({ f"{item_info} [{unit}]": records_one_item})
     

    df = pd.DataFrame.from_dict(records_all_items)
    #Datumszeile einfügen
    df.insert(0, "Date", f"{str(timestamp.tm_year)}/{str(timestamp.tm_mon)}/{str(timestamp.tm_mday)}" )

    #Endzeitstempel von Unix in "normales Zeitformat"
    endtimestamp = time.localtime(endtimestamp/ 10000000)
    year = endtimestamp[0]
    month = endtimestamp[1]
    day = endtimestamp[2]

    if folder_created:
        #Pandas Dataframe als Json exportieren
        if export_json.upper() == "YES": #Kommt aus der config.json
            file_created = df.to_json(path_or_buf=projektinfo["csv_path"]+ f"/{year}/{month}/{day}_processcalues.json")
        #Pandas Dataframe als CSV Exportieren
        if export_csv.upper() == "YES":#Kommt aus der config.json
            file_created = df.to_csv(path_or_buf=projektinfo["csv_path"]+ f"/{year}/{month}/{day}_processcalues.csv", sep=seperator, decimal = dec, )#sep und decimal kommt aus der config.json
        #file_created = write_json(path=projektinfo["csv_path"]+ f"/{year}_{month}_{day}_processcalues.json", data = records_all_items)
        print(f"{time.time()}: export erzeugt")


   
        return "done"
    else:
        return f"{time.time()}: no item named {item_info}"


