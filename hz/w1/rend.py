import sys, asyncio, subprocess, os, json
from playwright.async_api import async_playwright
d,f0,f1,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
st=json.load(open(f"{d}/timeline.json")); V=st["o"]=="v"; W,H=(1080,1920) if V else (1920,1080)
async def main():
    ff=subprocess.Popen(["ffmpeg","-y","-v","error","-f","image2pipe","-framerate","30","-c:v","mjpeg","-i","-","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-r","30",out+".tmp.mp4"],stdin=subprocess.PIPE)
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--allow-file-access-from-files","--no-sandbox"])
        pg=await b.new_page(viewport={"width":W,"height":H})
        await pg.goto(f"file://{os.path.abspath(d)}/built.html"); await pg.evaluate("window.ready"); await pg.wait_for_timeout(300)
        for f in range(f0,f1):
            await pg.evaluate(f"frame({f/30})"); ff.stdin.write(await pg.screenshot(type="jpeg",quality=92))
        await b.close()
    ff.stdin.close(); assert ff.wait()==0; os.rename(out+".tmp.mp4",out)
asyncio.run(main())
