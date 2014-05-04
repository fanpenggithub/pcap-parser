#coding=utf-8
__author__ = 'dongliu'

import json
import StringIO
import gzip


class Mime(object):
    def __init__(self, mime_str):
        if not mime_str:
            self.top_level = None
            self.subtype = None
            return
        idx = mime_str.find('/')
        if idx < 0:
            self.top_level = mime_str
            self.subtype = None
            return
        self.top_level = mime_str[:idx]
        self.subtype = mime_str[idx + 1:]


def try_print_json(text, output_file):
    if text is None:
        return
    if len(text) > 500000:
        # do not process to large text
        output_file.write(text)
        return False
    if text.startswith('{') and text.endswith('}') or text.startswith('{') and text.endswith('}'):
        # do not process a non-list-dict json
        try:
            data = json.loads(text)
            output_file.write(json.dumps(data, indent=2, ensure_ascii=False, separators=(',', ': ')).encode('utf-8'))
            return True
        except Exception as e:
            output_file.write(text)
            return False
    else:
        output_file.write(text)
        return False


def gzipped(content):
    """
    test if content is gzipped by magic num.
    """
    if content is not None and len(content) > 10 \
            and ord(content[0:1]) == 31 and ord(content[1:2]) == 139 \
            and ord(content[2:3]) == 8:
        return True
    return False


def ungzip(content):
    """ungzip content"""
    try:
        buf = StringIO.StringIO(content)
        gzip_file = gzip.GzipFile(fileobj=buf)
        content = gzip_file.read()
        return content
    except IOError:
        content = ungzip_carefully(content)
        return content
    except:
        import traceback
        traceback.print_exc()
        return content


def ungzip_carefully(content):
    """
    deal with corrupted gzip file, read one word once
    """
    compress_steam = StringIO.StringIO(content)
    gzip_file = gzip.GzipFile(fileobj=compress_steam)
    buf = StringIO.StringIO()
    try:
        while True:
            data = gzip_file.read(4)
            buf.write(data)
        return buf.getvalue()
    except IOError:
        return buf.getvalue()


def parse_http_header(header):
    header = header.strip()
    idx = header.find(':')
    if idx < 0:
        return None, None
    else:
        return header[0:idx].strip(), header[idx + 1:].strip()


def is_request(body):
    idx = body.find(' ')
    if idx < 0:
        return False
    method = body[0:idx].lower()
    return method in ('get', 'post', 'put', 'delete')


def is_response(body):
    return body.startswith('HTTP/') or body.startswith('http/')


def parse_content_type(content_type):
    if not content_type:
        return None, None
    idx = content_type.find(';')
    if idx < 0:
        idx = len(content_type)
    mime = content_type[0:idx]
    encoding = content_type[idx + 1:]
    if len(encoding) > 0:
        eidx = encoding.find('=')
        if eidx > 0:
            encoding = encoding[eidx + 1:]
        else:
            encoding = ''
    return mime.strip().lower(), encoding.strip().lower()


_text_mime_top_levels = {b'text'}
_text_mime_subtypes = {b'html', b'xml', b'json', b'javascript', b'ecmascript', b'atom+xml', b'rss+xml',
                       b'xhtml+xml', b'rdf+xml', b'x-www-form-urlencoded'}
def is_text(mime_str):
    mime = Mime(mime_str)
    return mime.top_level in _text_mime_top_levels or mime.subtype in _text_mime_subtypes


_binary_mime_top_levels = {'audio', 'image', 'video'}
_binary_mime_subtypes = {'octet-stream', 'pdf', 'postscript', 'zip', 'gzip'}


def is_binary(mime_str):
    mime = Mime(mime_str)
    return mime.top_level in _binary_mime_top_levels or mime.subtype in _binary_mime_subtypes


def decode_body(content, charset):
    if charset:
        try:
            return content.decode(charset).encode('utf-8')
        except:
            return content
    else:
        # todo: encoding detect
        try:
            return content.decode('utf-8').encode('utf-8')
        except:
            pass
        try:
            return content.decode('gb18030').encode('utf-8')
        except:
            pass
        return content