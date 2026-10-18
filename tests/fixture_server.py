"""Local stand-ins for the three external services used by script 15 --live/--llm.

Formats mirror the real services; CONTENT IS SYNTHETIC TEST DATA, not real weather or news.
  /forecast                 Open-Meteo forecast JSON (daily block)
  /rss                      PIB-style RSS 2.0 (UTF-8 BOM, HTML descriptions, a duplicate, off-topic items)
  /faithful/api/generate    Ollama /api/generate; rewrites the facts but keeps every number
  /hallucinate/api/generate Ollama /api/generate; rewrites the facts and changes one price
Run: python tests/fixture_server.py 8765
"""
import json, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

FORECAST = {"latitude": 13.125, "longitude": 80.25, "timezone": "Asia/Kolkata", "timezone_abbreviation": "GMT+5:30",
            "daily_units": {"time": "iso8601", "precipitation_sum": "mm", "temperature_2m_max": "°C", "temperature_2m_mean": "°C"},
            "daily": {"time": ["2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24"],
                      "precipitation_sum": [2.4, 18.6, 41.2, 7.9, 0.0, 12.3, 3.1],
                      "temperature_2m_max": [32.1, 30.4, 28.9, 30.2, 32.8, 31.5, 31.9],
                      "temperature_2m_mean": [28.4, 27.1, 26.0, 27.0, 28.6, 27.9, 28.2]}}

RSS = ('\ufeff<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>PIB (TEST FIXTURE)</title>'
       '<item><title>[TEST FIXTURE] Government reviews tomato and onion price situation</title>'
       '<link>https://pib.gov.in/PressReleasePage.aspx?PRID=0000001</link>'
       '<description>&lt;p&gt;Inter-ministerial committee reviews &lt;b&gt;market price&lt;/b&gt; trends of tomato and onion.&lt;/p&gt;</description>'
       '<pubDate>Sat, 17 Oct 2026 18:30:00 GMT</pubDate></item>'
       '<item><title>[TEST FIXTURE] Government reviews tomato and onion price situation</title>'
       '<link>https://pib.gov.in/PressReleasePage.aspx?PRID=0000001</link><description>duplicate</description>'
       '<pubDate>Sat, 17 Oct 2026 18:30:00 GMT</pubDate></item>'
       '<item><title>[TEST FIXTURE] Northeast monsoon advisory issued for horticulture growers</title>'
       '<link>https://pib.gov.in/PressReleasePage.aspx?PRID=0000002</link>'
       '<description>Advisory on rainfall and crop protection for vegetable growers.</description>'
       '<pubDate>Fri, 16 Oct 2026 11:00:00 GMT</pubDate></item>'
       '<item><title>[TEST FIXTURE] Minister inaugurates new railway station</title>'
       '<link>https://pib.gov.in/PressReleasePage.aspx?PRID=0000003</link><description>Transport infrastructure.</description>'
       '<pubDate>Fri, 16 Oct 2026 09:00:00 GMT</pubDate></item>'
       '</channel></rss>')


def rewrite(prompt, corrupt=False):
    facts = prompt.split('\n\n', 1)[1]
    out = facts.replace('# AgriSight Market Intelligence Brief', '# Buyer Brief — AgriSight')
    out = re.sub(r'Price data through (\d{4})-(\d{2})-(\d{2})\.',
                 lambda m: f"Prices are current to {int(m.group(3))} {['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][int(m.group(2))]} {m.group(1)}.", out)
    out = out.replace('## Price outlook', '## What prices are doing').replace('current ', 'now ')
    if corrupt:
        out = out.replace('2750.00', '2950.00', 1)  # a plausible-looking but wrong Tomato price
    return out


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        b = body.encode('utf-8') if isinstance(body, str) else body
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        ua = self.headers.get('User-Agent', '')
        if 'Python-urllib' in ua:  # behave like sites that block the default client
            return self._send(403, 'Forbidden', 'text/plain')
        if self.path.startswith('/forecast'): return self._send(200, json.dumps(FORECAST), 'application/json')
        if self.path.startswith('/rss'): return self._send(200, RSS, 'application/rss+xml; charset=utf-8')
        self._send(404, 'not found', 'text/plain')

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path.endswith('/api/generate') and body.get('stream') is False:
            text = rewrite(body['prompt'], corrupt=self.path.startswith('/hallucinate'))
            return self._send(200, json.dumps({'model': body['model'], 'response': text, 'done': True}), 'application/json')
        self._send(400, 'bad request', 'text/plain')

    def log_message(self, *a): pass


if __name__ == '__main__':
    HTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8765), H).serve_forever()
