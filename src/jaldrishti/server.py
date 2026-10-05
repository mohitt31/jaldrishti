"""Local interactive query service. API keys and PDFs stay on the server."""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

WEB = Path(__file__).with_name('web')


def make_handler(session):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send(self, status, body, kind='application/json; charset=utf-8'):
            if not isinstance(body, bytes): body=json.dumps(body,ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers();self.wfile.write(body)
        def same_origin(self):
            host=self.headers.get('Host','')
            allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            origin=self.headers.get('Origin')
            return host in allowed and (not origin or origin in {'http://'+h for h in allowed})
        def do_GET(self):
            if not self.same_origin(): return self.send(403,{'error':'Local access only'})
            if self.path=='/api/status':
                return self.send(200,{'version':'0.3.0','mode':'bounded live search' if not session.api.offline else 'offline cached search',
                    'live_credits':session.api.live_credits,'live_attempts':session.api.live_attempts,'live_limit':session.api.max_live_searches or 0})
            routes={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','application/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
            if self.path not in routes:return self.send(404,{'error':'Not found'})
            name,kind=routes[self.path];self.send(200,(WEB/name).read_bytes(),kind)
        def do_POST(self):
            if not self.same_origin():return self.send(403,{'error':'Local access only'})
            if self.path!='/api/ask':return self.send(404,{'error':'Not found'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'Use application/json'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=8192:raise ValueError()
                payload=json.loads(self.rfile.read(length))
                question=payload.get('question','')
                mode=payload.get('mode','library')
                if mode not in ('library','reference'):raise ValueError()
                if not isinstance(question,str) or not 3<=len(question.strip())<=1500:raise ValueError()
            except (ValueError,TypeError,AttributeError):return self.send(400,{'error':'Enter a question between 3 and 1500 characters'})
            try:
                result=session.run(question.strip(),mode,budget=2)
                self.send(200,result)
            except Exception:
                # Request exceptions can contain credential-bearing URLs; never return them.
                self.send(503,{'error':'Query could not complete. The search limit may be reached or a source unavailable. No answer is asserted.'})
    return Handler


def serve(port=8766,live_searches=0):
    if not 0<=live_searches<=3:raise ValueError('Choose 0–3 live searches per server session')
    from .pipeline import Session
    session=Session(live=live_searches>0,offline=live_searches==0)
    session.api.max_live_searches=live_searches
    session.library_docs()
    with HTTPServer(('127.0.0.1',port),make_handler(session)) as server:
        print(f'NeerTathya v0.3: http://127.0.0.1:{server.server_port} — live search cap {live_searches}',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
