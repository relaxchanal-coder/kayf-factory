"""Fetch candidate free-licensed images from Wikimedia Commons for hz stories (run on GitHub runner)."""
import json, os, re, sys, time, urllib.parse, urllib.request
UA={"User-Agent":"KayfFactory/1.0 (https://github.com/relaxchanal-coder/kayf-factory; educational videos)"}
OK=("public domain","pd","cc0","cc by","cc-by")
BAD=re.compile(r"(corpse|dead body|blood|wound|nude|logo|icon|flag|coat of arms|signature)",re.I)
def get(u):
    for i in range(5):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
        except Exception as e:
            if i==4: raise
            time.sleep(5*(i+1))
def strip(h): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>","",h or "")).strip()
Q=json.load(open(sys.argv[1])); out=sys.argv[2]; os.makedirs(out,exist_ok=True); meta={}
for key,query in Q.items():
    p={"action":"query","format":"json","prop":"imageinfo","iiprop":"url|extmetadata|size|mime","iiurlwidth":1600}
    if query.startswith("File:"): p["titles"]=query
    else: p.update(generator="search",gsrsearch=f"{query} filetype:bitmap",gsrnamespace=6,gsrlimit=15)
    try: d=json.loads(get("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(p)))
    except Exception as e: print("ERR",key,e); continue
    pages=sorted(d.get("query",{}).get("pages",{}).values(),key=lambda x:x.get("index",0)); n=0
    for pg in pages:
        ii=(pg.get("imageinfo") or [{}])[0]; m=ii.get("extmetadata",{}); lic=m.get("LicenseShortName",{}).get("value","")
        if ii.get("mime") not in ("image/jpeg","image/png") or ii.get("width",0)<700: continue
        if not any(x in lic.lower() for x in OK): continue
        if BAD.search(pg["title"]): continue
        try:
            raw=get(ii.get("thumburl") or ii["url"]); f=f"{key}_{n}.jpg"; open(f"{out}/{f}","wb").write(raw)
        except Exception as e: print("dl fail",e); continue
        meta[f]={"title":pg["title"],"artist":strip(m.get("Artist",{}).get("value"))[:80],"license":lic,"w":ii["width"],"h":ii["height"]}
        n+=1; time.sleep(1)
        if n>=4: break
    print(key,n); time.sleep(1)
json.dump(meta,open(f"{out}/meta.json","w"),ensure_ascii=False,indent=1)
