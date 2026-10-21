import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from assistant import answer, COURSES, ROOT

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/api/courses':
            self.send_json([{'id':c['id'],'title':c['title']} for c in COURSES]); return
        if self.path not in ('/','/index.html'):
            self.send_error(404); return
        data=(ROOT/'index.html').read_bytes()
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(data)
    def send_json(self,obj,status=200):
        b=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        if self.path!='/api/ask': self.send_error(404); return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=16384: raise ValueError('Некорректный размер запроса')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data.get('question'),str): raise ValueError('Вопрос должен быть строкой')
            self.send_json(answer(data['question'],data.get('course') or None))
        except (ValueError,TypeError,AttributeError) as e: self.send_json({'error':str(e)},400)

if __name__=='__main__':
    print('Откройте http://127.0.0.1:8765')
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
