import socketserver
import http.server
import urllib.request
import os
import sys

class CameraProxy(http.server.SimpleHTTPRequestHandler):
    BaseUri = None
    Username = None
    Password = None
    Port = 9097
    Opener = None
    def do_GET(self):
        url=CameraProxy.BaseUri + self.path[1:]
        try:
            rsp = None
            if CameraProxy.Opener != None :
                rsp = CameraProxy.Opener.open(url)
            else:
                rsp = urllib.request.urlopen(url)
            self.send_proxy_response(rsp)
        except urllib.error.HTTPError as e:
            self.send_proxy_response(e)

    def send_proxy_response(self, rsp):
        try:
            self.send_response(rsp.code)
            for l in str(rsp.headers).splitlines():
                if not l:
                    continue
                key, value = l.split(":", 1)
                self.send_header(key, value)
            self.end_headers()
            self.copyfile(rsp, self.wfile)
        except ConnectionError as e:
            pass # Client drop connection. Ignore.

CameraProxy.BaseUri = os.getenv("CAMERA_PROXY_URI")
CameraProxy.Username = os.getenv("CAMERA_PROXY_USERNAME")
CameraProxy.Password = os.getenv("CAMERA_PROXY_PASSWORD")
CameraProxy.Port = int(os.getenv("CAMERA_PROXY_PORT", CameraProxy.Port))

if not CameraProxy.BaseUri:
    print ("Please, provide CAMERA_PROXY_URI variable")
    sys.exit(1)

if CameraProxy.Username and CameraProxy.Password:
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, CameraProxy.BaseUri,
                              CameraProxy.Username, CameraProxy.Password)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr);
    opener = urllib.request.build_opener(handler);

    CameraProxy.Opener = opener

httpd = socketserver.ForkingTCPServer(('', CameraProxy.Port), CameraProxy)

print ("Now serving at", str(CameraProxy.Port))
httpd.serve_forever()
