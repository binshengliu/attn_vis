import argparse
import html
import io
import os
import sys
import urllib
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse


class S(SimpleHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        parsed = urlparse(self.path)
        path = "." + parsed.path
        if os.path.isdir(path):
            self.copyfile(self.list_directory(path), self.wfile)
            return
        elif path.endswith(".html"):
            path = os.path.basename(path)[:-5] + ".json"
            with open("index.html", "r") as f:
                html = f.read()
                html = html.replace("attn_vis_data.json", path)
                self.wfile.write(html.encode("utf8"))
        else:
            try:
                with open(path, "rb") as f:
                    self.wfile.write(f.read())
            except OSError:
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return None

        # with open("index.html") as f:
        #     self.wfile.write(f.read().encode("utf8"))

    def do_HEAD(self):
        self._set_headers()

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        r = []
        try:
            displaypath = urllib.parse.unquote(self.path, errors="surrogatepass")
        except UnicodeDecodeError:
            displaypath = urllib.parse.unquote(path)
        displaypath = html.escape(displaypath, quote=False)
        enc = sys.getfilesystemencoding()
        title = "Directory listing for %s" % displaypath
        r.append(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
            '"http://www.w3.org/TR/html4/strict.dtd">'
        )
        r.append("<html>\n<head>")
        r.append(
            '<meta http-equiv="Content-Type" ' 'content="text/html; charset=%s">' % enc
        )
        r.append("<title>%s</title>\n</head>" % title)
        r.append("<body>\n<h1>%s</h1>" % title)
        r.append("<hr>\n<ul>")
        for name in list:
            fullname = os.path.join(path, name)
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = linkname = name + "/"
            elif os.path.isfile(fullname) and name.endswith(".json"):
                displayname = linkname = name[:-5] + ".html"
            else:
                continue

            if os.path.islink(fullname):
                displayname += "@"
                # Note: a link to a directory displays with @ and links with /
            r.append(
                '<li><a href="%s">%s</a></li>'
                % (
                    urllib.parse.quote(linkname, errors="surrogatepass"),
                    html.escape(displayname, quote=False),
                )
            )
        r.append("</ul>\n<hr>\n</body>\n</html>\n")
        encoded = "\n".join(r).encode(enc, "surrogateescape")
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f


def run(server_class=HTTPServer, handler_class=S, addr="localhost", port=8000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    print(f"Starting httpd server on {addr}:{port}")
    httpd.serve_forever()


def parse_arguments():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-l", "--listen", default="localhost")
    parser.add_argument("-p", "--port", default=8000, type=int)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    run(addr=args.listen, port=args.port)
