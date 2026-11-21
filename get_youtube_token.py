"""(اختياري) استخراج YT_REFRESH_TOKEN للرفع التلقائي على يوتيوب.

شغّله مرة واحدة على كمبيوتر:
    python get_youtube_token.py CLIENT_ID CLIENT_SECRET
سيفتح المتصفح، توافق على الصلاحية، ويطبع لك الـ refresh token.
"""
import http.server
import sys
import urllib.parse
import webbrowser

import requests

cid, secret = sys.argv[1], sys.argv[2]
redirect = "http://localhost:8765"
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cid, "redirect_uri": redirect, "response_type": "code", "access_type": "offline",
    "prompt": "consent", "scope": "https://www.googleapis.com/auth/youtube.upload"})
code = {}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        code["c"] = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("code", [""])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write("تم! ارجع للنافذة السوداء.".encode())


print("افتح هذا الرابط إذا ما انفتح تلقائياً:\n", url)
webbrowser.open(url)
http.server.HTTPServer(("localhost", 8765), H).handle_request()
r = requests.post("https://oauth2.googleapis.com/token", data={
    "code": code["c"], "client_id": cid, "client_secret": secret,
    "redirect_uri": redirect, "grant_type": "authorization_code"}).json()
print("\nYT_REFRESH_TOKEN =", r.get("refresh_token") or r)
