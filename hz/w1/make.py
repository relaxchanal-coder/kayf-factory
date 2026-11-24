import json, sys, os, asyncio, subprocess, certifi
import os as _o
if _o.path.exists("/root/.ccr/ca-bundle.crt"): certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
HZ=_o.environ.get("HZ_ROOT","/home/claude/hz"); NM=_o.environ.get("NM","/home/claude/fb/node_modules"); F="file://"+NM+"/@fontsource"
def sh(c): subprocess.run(c,shell=True,check=True)
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]))
async def tts(d,S):
    import edge_tts
    sem=asyncio.Semaphore(4)
    async def one(i,s):
        async with sem:
            for a in range(5):
                try:
                    c=edge_tts.Communicate(s["say"],"ar-SA-HamedNeural",rate="+12%",pitch="-6Hz",boundary="WordBoundary",proxy=os.environ["HTTPS_PROXY"])
                    W=[]
                    with open(f"{d}/au/n{i}.mp3","wb") as fh:
                        async for ch in c.stream():
                            if ch["type"]=="audio": fh.write(ch["data"])
                            elif ch["type"]=="WordBoundary": W.append({"w":ch["text"],"t":ch["offset"]/1e7,"d":ch["duration"]/1e7})
                    if W: return W
                except Exception as e: print("tts retry",e); await asyncio.sleep(3)
            raise SystemExit("tts failed")
    return await asyncio.gather(*[one(i,s) for i,s in enumerate(S)])
TH={
"r1":dict(poff=0,acc="#4fd1a1",acc2="#b8f5dc",txt="#eef7f0",txt2="#cfe6d8",txt3="#9cbfac",bg=("#0b2a20","#06150f","#020805"),land="#17382b",pat="stars",Q="reem-kufi",A="amiri",rad="6px"),
"r2":dict(poff=3,acc="#7fb2ff",acc2="#cfe0ff",txt="#eef3ff",txt2="#cdd8f0",txt3="#9aa9c9",bg=("#0f1d3d","#070e22","#02050d"),land="#1a2a4f",pat="grid",Q="aref-ruqaa",A="amiri",rad="22px"),
"r3":dict(poff=6,acc="#3fd0c9",acc2="#b6f2ee",txt="#effaf9",txt2="#cde9e6",txt3="#93b9b5",bg=("#0a2a2c","#051517","#010708"),land="#123b3c",pat="hex",Q="reem-kufi",A="cairo",rad="40px"),
"r4":dict(poff=1,acc="#e8925a",acc2="#ffd2b0",txt="#fbefe6",txt2="#ecd4c3",txt3="#bb9b85",bg=("#2a160c","#140a05","#050201"),land="#3b2416",pat="rings",Q="baloo-bhaijaan-2",A="cairo",rad="4px"),
"r5":dict(poff=4,acc="#ff6b6b",acc2="#ffc9c9",txt="#fff1f0",txt2="#f0d0cd",txt3="#c39a97",bg=("#2e0b10","#160407","#060102"),land="#3d1419",pat="arches",Q="aref-ruqaa",A="amiri",rad="14px"),
"r6":dict(poff=7,acc="#c49bff",acc2="#e8d8ff",txt="#f6f0ff",txt2="#ddd0ef",txt3="#a897c0",bg=("#231338","#110820","#04020a"),land="#2c1b45",pat="squares",Q="marhey",A="amiri",rad="30px"),
"r7":dict(poff=2,acc="#d2600f",acc2="#8a3a05",txt="#2a1d12",txt2="#4a3a2a",txt3="#6d5c4a",bg=("#fbf4e6","#efe3cb","#e2d2b2"),land="#e6d5b3",pat="rays",Q="cairo",A="cairo",rad="18px"),
"L-":dict(poff=5,acc="#cfd8e3",acc2="#ffffff",txt="#f2f5f8",txt2="#d2dae3",txt3="#9aa6b3",bg=("#1b2230","#0d1118","#030507"),land="#263040",pat="stars",Q="aref-ruqaa",A="amiri",rad="10px"),
}
def rgb(h): h=h.lstrip("#"); return ",".join(str(int(h[i:i+2],16)) for i in (0,2,4))
def theme(s,th):
    fp=lambda f,w: F+f"/{f}/files/{f}-arabic-{w}-normal.woff2"
    s=s.replace("url(__FONTS__/aref-ruqaa-arabic-700-normal.woff2)","url("+fp(th["Q"],700)+")").replace("url(__FONTS__/amiri-arabic-700-normal.woff2)","url("+fp(th["A"],700)+")").replace("url(__FONTS__/amiri-arabic-400-normal.woff2)","url("+fp(th["A"],400)+")")
    for a,b in [("236,200,106",rgb(th["acc"])),("#ecc86a",th["acc"]),("#f6dfa0",th["acc2"]),("#f4ead2",th["txt"]),("#e6dac0",th["txt2"]),("#bfae8c",th["txt3"]),
                ("#1d150a",th["bg"][0]),("#0d0905",th["bg"][1]),("#030201",th["bg"][2]),("#382a17",th["land"]),("#3a2a14",th["land"]),("#0b0703",th["bg"][2]),("border-radius:22px","border-radius:"+th["rad"])]:
        s=s.replace(a,b)
    if th.get("light"):
        s=s.replace("rgba(0,0,0,.45)","rgba(255,255,255,.8)").replace("rgba(0,0,0,.5)","rgba(255,255,255,.75)")
        s=s.replace("</style>",".a,.a *,.q{text-shadow:none !important}.card{box-shadow:0 10px 30px rgba(120,80,30,.18)!important;background:rgba(255,255,255,.55)!important}</style>")
    return s
def build(d):
    st=json.load(open(f"{d}/story.json")); S=st["scenes"]; os.makedirs(f"{d}/au",exist_ok=True)
    if not os.path.exists(f"{d}/words.json"):
        json.dump(asyncio.run(tts(d,S)),open(f"{d}/words.json","w"),ensure_ascii=False)
    WS=json.load(open(f"{d}/words.json")); t=0.6
    for i,s in enumerate(S):
        L=dur(f"{d}/au/n{i}.mp3"); s["start"]=round(t,3); s["voice"]=round(t+0.25,3); s["words"]=WS[i]
        s["dur"]=round(L+(0.55 if s["type"]!="outro" else 1.6),3); t+=s["dur"]
    st["total"]=round(t+0.3,3); st["img"]="file:///nonexistent"; st["logo"]="file://"+HZ+"/logo.png"
    json.dump(st,open(f"{d}/timeline.json","w"),ensure_ascii=False)
    s=open(HZ+"/engine/story4.html").read()
    V=st["o"]=="v"; s=s.replace("__W__","1080" if V else "1920").replace("__H__","1920" if V else "1080")
    key=os.path.basename(d.rstrip("/"))[:2]; th=TH.get(key) or dict(TH[["r1","r3","r6","r2","r5","r4","L-"][sum(map(ord,key))%7]],poff=sum(map(ord,key))%8)
    fp=lambda f,w: F+f"/{f}/files/{f}-arabic-{w}-normal.woff2"
    s=s.replace("__QFONT__",fp(th["Q"],700)).replace("__AFONT__",fp(th["A"],700))
    s=s.replace("__ILL__",open(HZ+"/engine/ill.js").read())
    s=s.replace("__D3__",NM+"/d3/dist/d3.min.js").replace("__TOPO__",NM+"/topojson-client/dist/topojson-client.min.js")
    st["poff"]=th.get("poff",0); st["rad"]=th["rad"]
    s=s.replace("__WORLD__",open(NM+"/world-atlas/countries-50m.json").read()).replace("__DATA__",json.dumps(st,ensure_ascii=False))
    open(f"{d}/built.html","w").write(s); return st
def audio(d,st):
    S=st["scenes"]; ins=[];fl=[]
    for i,s in enumerate(S):
        ins+=["-i",f"{d}/au/n{i}.mp3"]; ms=int(s["voice"]*1000); fl.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[v{i}]")
    n=len(S); T=st["total"]
    fl.append("".join(f"[v{i}]" for i in range(n))+f"amix=inputs={n}:normalize=0,apad,atrim=0:{T}[voice]")
    # pad: warm drone + whooshes at scene starts
    pad=f"aevalsrc='0.05*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.08*t))+0.035*sin(2*PI*82.5*t)+0.02*sin(2*PI*110*t+sin(2*PI*0.2*t))':s=48000:d={T}"
    fl.append(f"{pad},aformat=channel_layouts=stereo,afade=t=in:d=1.5,afade=t=out:st={T-2}:d=2[pad0]")
    wh=[];
    for i,s in enumerate(S[1:],1):
        ms=int(max(0,s["start"]-0.35)*1000)
        fl.append(f"anoisesrc=c=pink:a=0.25:d=0.7:s=48000,bandpass=f=1400:w=1200,afade=t=in:d=0.35,afade=t=out:st=0.35:d=0.35,aformat=channel_layouts=stereo,adelay={ms}|{ms}[w{i}]"); wh.append(f"[w{i}]")
    fl.append(f"[voice]asplit[vo][sc]")
    fl.append(f"[pad0][sc]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400[padd]")
    fl.append("[vo][padd]"+"".join(wh)+f"amix=inputs={2+len(wh)}:normalize=0,atrim=0:{T},loudnorm=I=-14:TP=-1.5[out]")
    sh("ffmpeg -y -v error "+" ".join(ins)+f" -filter_complex \"{';'.join(fl)}\" -map [out] -c:a pcm_s16le {d}/mix.wav")
if __name__=="__main__":
    d=sys.argv[1]; st=build(d); audio(d,st); print(d, "total", st["total"])
