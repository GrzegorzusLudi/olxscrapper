import sys
import json
import requests
import os
import re
from PIL import Image, ImageDraw

danemiast_nazwa = "danemiast.txt"
if not os.path.isfile(danemiast_nazwa):
    with open(danemiast_nazwa,"w") as f:
        f.write("{}")
    known = {}
else:
    with open(danemiast_nazwa) as f:
        known = json.loads(f.read())


granice = [14.0,55.5,24.5,48.5]

rozmiaryObrazu = (750,750)

MAX_PAGES_SCRAPPED = 12

def rysujWielokat(coords,draw,width):
    wielokat = coords[0]
    lastpoint = None
    for point in wielokat:
        if lastpoint != None:
            c = ((lastpoint[0]-granice[0])/(granice[2]-granice[0])*rozmiaryObrazu[0],(lastpoint[1]-granice[1])/(granice[3]-granice[1])*rozmiaryObrazu[1],(point[0]-granice[0])/(granice[2]-granice[0])*rozmiaryObrazu[0],(point[1]-granice[1])/(granice[3]-granice[1])*rozmiaryObrazu[1])
            draw.line(c,fill=255,width=width)
        lastpoint = point
    
def rysujGeoJson(plik,draw,width):    
    with open(plik) as f:
        kontur = json.loads(f.read())
        
    for feature in kontur['features']:
        
        if feature['geometry']['type'] == 'MultiPolygon':
            for wielokat in feature['geometry']['coordinates']:
                rysujWielokat(wielokat,draw,width)
        elif feature['geometry']['type'] == 'Polygon':
            rysujWielokat(feature['geometry']['coordinates'],draw,width)

def koordynaty(miasto):
    if(miasto in known):
        return known[miasto]
    try:
        url = 'https://pl.wikipedia.org/wiki/'+miasto
        print("Checking "+url)
        r = requests.get(url)
        t = r.text
        coords = re.findall(r"wgCoordinates\":{\"lat\":[0-9\.]+,\"lon\":[0-9\.]+}",t)
        coor = re.findall(r"[0-9\.]+",coords[0])
        known[miasto] = coor
        
        with open(danemiast_nazwa,"w") as f:
            f.write(json.dumps(known))
        return coor
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except:
        known[miasto] = None
        with open(danemiast_nazwa,"w") as f:
            f.write(json.dumps(known))
        return None

if len(sys.argv) < 2:
    print("Nazwa narzędzia musi być wyróżniona!")
    exit()




#SCRAPPER

miasta = []

nazwa = '-'.join(sys.argv[1:])
url = 'https://www.olx.pl/oferty/q-'+nazwa+'/?spellchecker=off'
r = requests.get(url)
print("checking "+url)
tekst = r.text

pagelength = int(re.findall(r"[0-9]+",re.findall(r"pageCount=[0-9]+",tekst)[0])[0])
for pageno in range(1,min(pagelength+1,MAX_PAGES_SCRAPPED)):
    url = 'https://www.olx.pl/oferty/q-'+nazwa+'/?spellchecker=off&page='+str(pageno)
    print("checking "+url)
    r = requests.get(url)
    page = r.text
    miejscowości = re.findall(r"<p class=\"lheight16\">\s*<small class=\"breadcrumb x-normal\">\s*<span>\s*<i data-icon=\"location-filled\"></i>[A-zĄĆĘŁŃÓŚŹŻąćęłńóśźż -]+\s*",page)
    for filtered in miejscowości:
        nazw = re.findall(r"[A-zĄĆĘŁŃÓŚŹŻąćęłńóśźż -]+$",filtered)[0].strip()
        miasta.append(nazw)

miasta = list(set(miasta))

im = Image.new('RGBA', rozmiaryObrazu, (255, 255, 255, 255))

draw = ImageDraw.Draw(im)
rysujGeoJson("poland2.geojson",draw,1)
rysujGeoJson("poland.geojson",draw,2)

zostało = len(miasta)
i = 1
for miasto in miasta:
    koords = koordynaty(miasto)
    print(str(i)+'/'+str(zostało))
    i+=1
    if koords != None:
        y_,x_ = float(koords[0]),float(koords[1])
        x,y = (x_-granice[0])/(granice[2]-granice[0])*rozmiaryObrazu[0],(y_-granice[1])/(granice[3]-granice[1])*rozmiaryObrazu[1]
        draw.rectangle(((x-5,y-5), (x+5,y+5)), fill="red")



im.save(nazwa+".png")







