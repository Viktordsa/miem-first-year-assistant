import json,threading,unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from server import Handler

class HttpTests(unittest.TestCase):
    def test_browser_api(self):
        http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=http.serve_forever,daemon=True);worker.start()
        base=f'http://127.0.0.1:{http.server_port}'
        try:
            with urlopen(base) as r:self.assertEqual(r.status,200)
            with urlopen(base+'/api/courses') as r:self.assertEqual(len(json.load(r)),25)
            data=json.dumps({'question':'Какая формула оценивания?','course':'1197128597'}).encode()
            with urlopen(Request(base+'/api/ask',data=data)) as r:
                a=json.load(r);self.assertIn('0.35',a['answer']);self.assertTrue(a['sources'])
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(base+'/api/ask',data=b'{broken'))
            self.assertEqual(error.exception.code,400)
        finally:
            http.shutdown();http.server_close();worker.join()

if __name__=='__main__':unittest.main()
