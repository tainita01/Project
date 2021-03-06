import urllib2, json
from geopy import geocoders

import arcpy
from arcpy import env
arcpy.env.overwriteOutput = True
env.workspace = "F:/UWTacoma/GIS_501_AU_2014/Project/"
path = "F:/UWTacoma/GIS_501_AU_2014/Project/"
fc = "WAbusco.shp"
el = "URloc.shp"
spatialref = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"

def geo(location):
        g = geocoders.GoogleV3()
        loc = g.geocode(location)
        return loc.latitude, loc.longitude

#Create a Feature Class of URLoc with defined Fields:
arcpy.management.CreateFeatureclass(path, el, "POINT","","","",spatialref)
arcpy.management.AddField(el, "Latitude", "FLOAT")
arcpy.management.AddField(el, "Longitude", "FLOAT")
arcpy.management.AddField(el, "ADDRESS", "TEXT")
arcpy.management.AddField(el, "ZIP", "LONG")

#Use Insert Cursor to populate the Feature Class table:
cur = arcpy.da.InsertCursor(el, ["SHAPE@XY","Latitude","Longitude", "ADDRESS", "ZIP"])
try:
        print("Search for motorcoach carriers in your area")
        address = raw_input("Please enter your street address: ")
        place = raw_input("and please enter your 5-digit zip code:")
        location = '%s  %s' % (address, place)
        (Latitude, Longitude) = geo(location)
        print '(' + str(Latitude) +', ' + str(Longitude)+')'
        row = [(Longitude,Latitude),Latitude,Longitude,address,place]
        cur.insertRow(row)
        
except ValueError:
        print("Error: geocode failed on input %s with message %s"%(location, error_message))


#Create a Feature Class of Motorcoach Carriers with defined Fields:
arcpy.management.CreateFeatureclass(path, fc, "POINT","","","",spatialref)
arcpy.management.AddField(fc, "Latitude", "FLOAT")
arcpy.management.AddField(fc, "Longitude", "FLOAT")
arcpy.management.AddField(fc, "Name", "TEXT")
arcpy.management.AddField(fc, "Telephone", "TEXT")

#Use Insert Cursor to populate the Feature Class table:
cur = arcpy.da.InsertCursor(fc, ["SHAPE@XY","Latitude","Longitude", "Name", "Telephone"])

#Defining Search terms and SaferBus API keys:
num=0

while num<1000:
        try:
        
                upath = 'https://mobile.fmcsa.dot.gov/saferbus/resource/v1/carriers/state/'
                state = 'WA'
                extension = '.json'
                carrierType = '?carrierType=MC'
                resultsegment = '&start=' + str(num) + '&size=25&'
                webKey = 'webKey=76e93c56d8d2798badea4202033a2b372a6528e8'
                url = upath + state + extension + carrierType + resultsegment + webKey
                libopen = urllib2.urlopen(url)#file-like object
                stuff = json.load(libopen) 
                keys = stuff['Carriers']['Carrier'][0]


#Iterating through the carriers for ones with defined Places:
        
                if keys['allowToOperate']=="Y":
                        try:
                                location = json.dumps(keys['phyStreet'], default= str) + ' ' + json.dumps(keys['phyZip'], default = str)
                                (Latitude, Longitude) = geo(location)
                                print '(' + str(Latitude) +', ' + str(Longitude)+')'
                        except ValueError:
                                print("Error: geocode failed on input %s with message %s"%(json.dumps(stuff['Carriers']['Carrier'], default=str), error_message))
                                continue
        
        
#Defining the items contained in each row:
                        for row in keys:
                                Telephone = json.dumps(keys['telephone'], default=str)
                                if keys.has_key('dbaName'):
                                        Name = json.dumps(keys['dbaName'], default=str)
                                else:
                                        Name = json.dumps(keys["legalName"], default=str)

                        row = [(Longitude,Latitude),Latitude,Longitude,Name,Telephone]
                        cur.insertRow(row)
                        num+=1
                        continue
                else:
                        print( "Not allowed to operate.")
                        num+=1
                        continue
        except KeyError:
                print("No more records")
                break
        break

arcpy.management.MakeFeatureLayer('WAbusco.shp', 'WAbusco_lyr')

#Select by Location with a US cartographic boundary shapefile in WGS 1984 projection:
arcpy.management.SelectLayerByLocation('WAbusco_lyr', 'WITHIN_A_DISTANCE', 'URloc.shp', "16 kilometers")

#Check selection and create a new shapefile:
matchcount = int(arcpy.GetCount_management('WAbusco_lyr').getOutput(0)) 
if matchcount == 0:
    print('no features matched spatial and attribute criteria')
else:
    arcpy.CopyFeatures_management('WAbusco_lyr', 'BUSNearU')

                
