import csv
import sys
import socket
import socks
import requests
import time
import json
import os
import inspect
import pprint
from datetime import datetime, timezone
import pytz
import core_util
import logging
import persontoken

REQ_TIMEOUT = 6
REQ_SLEEP = 0.5
LOCAL_TZ = 'Asia/Shanghai'

requests.adapters.DEFAULT_RETRIES = 5

# sleep time should be set properly. Please following the Github restriction.
# If not, you will see below message.
#
# {
#     "message": "API rate limit exceeded for xxx.xxx.xxx.xxx.
#                 (But here's the good news: Authenticated requests get a higher rate limit.
#                 Check out the documentation for more details.)",
#     "documentation_url": "https://developer.github.com/v3/#rate-limiting"
# }
SP_GITHUB_HEADER = {
    'User-Agent': 'Mozilla/5.0 ven(Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/69.0.3497.100 Safari/537.36',
    'Accept': 'application/vnd.github.VERSION.text+json'
}

SIMPLE_HEADER = {
    'User-Agent': 'Mozilla/5.0 ven(Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/69.0.3497.100 Safari/537.36'
}


def get_gh_header(token=persontoken.get_token()):
    SP_GITHUB_HEADER['Authorization'] = f'token {token}'
    return SP_GITHUB_HEADER


def std_table_name(repo_url, separation):
    tmp = separation.join(repo_url.split("/")[-2:]).replace("-", "_")
    result = ''.join([i for i in tmp if not i.isdigit()])
    return result


def read_xsv(path, separator, encoding='utf-8'):
    logger = logging.getLogger("StreamLogger")
    logger.info(f"read xsv [{encoding}] -- {path}")
    out = []
    with open(path, 'r', encoding=encoding) as _f:
        tsvreader = csv.reader(_f, delimiter=separator)
        for line in tsvreader:
            out.append(list(s.strip() for s in line if s.strip() != ''))
    return out


def dump_xsv(path, data, separator, header=None, encoding='utf-8'):
    logger = logging.getLogger("StreamLogger")
    logger.info(f"dump xsv [{encoding}] -- {path}")
    with open(path, 'w', encoding=encoding, newline='') as _f:
        tsvwriter = csv.writer(_f, delimiter=separator)
        if header is not None:
            tsvwriter.writerow(header)
        tsvwriter.writerows(data)


def read_tsv(path, encoding='utf-8'):
    return read_xsv(path, "\t", encoding=encoding)


def dump_tsv(path, data, header=None, encoding='utf-8'):
    dump_xsv(path, data, "\t", header=header, encoding=encoding)


def read_csv(path, encoding='utf-8'):
    return read_xsv(path, ",", encoding=encoding)


def dump_csv(path, data, header=None, encoding='utf-8'):
    dump_xsv(path, data, ",", header=header, encoding=encoding)


def get_col(a_list, col):
    if type(col) == int:
        return [row[col] for row in a_list]
    elif type(col) == list:
        return [[row[c] for c in col] for row in a_list]


def humanbytes(B):
    """
    Return the given bytes as a human friendly KB, MB, GB, or TB string
    :param B: Byte value
    :return: human friendly string
    """
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.3f} MB'.format(B / MB)
    elif GB <= B < TB:
        return '{0:.4f} GB'.format(B / GB)
    elif TB <= B:
        return '{0:.4f} TB'.format(B / TB)


class Reload:
    """
    For redirect standard output
    """

    def __init__(self, path=None, postfix=None):
        if path is None:
            caller = inspect.stack()[1].filename
            now_time = str(datetime.now().isoformat())
            now_time = now_time.replace(":", "")
            now_time = now_time.replace(".", "")
            if postfix is None:
                postfix = ""
            else:
                postfix += "_"
            path = drop_file_ext(caller) + "_" + postfix + now_time + ".log"
        print("-" * 20, "Reload to", path, "-" * 20, flush=True)
        self.orig_stdout = sys.stdout
        self.opened = True
        self.log_file = open(path, 'w', encoding='utf8')
        sys.stdout = self

    def write(self, message):
        self.orig_stdout.write(message)
        self.log_file.write(message)

    def flush(self):
        self.orig_stdout.flush()
        self.log_file.flush()

    def close(self):
        if self.opened:
            print("-" * 20, "End of Reload", "-" * 20, flush=True)
            sys.stdout = self.orig_stdout
            self.log_file.close()
            self.opened = False
            print("End reload", flush=True)
        else:
            print("Already closed", flush=True)

    def __del__(self):
        self.close()
        print("Close by __del__", flush=True)


def drop_file_ext(file_path):
    """
    get basename and drop file extension
    :param file_path: file path
    :return: file name without extension
    """
    return os.path.splitext(os.path.basename(file_path))[0]


class SS:
    """
    For proxy
    """

    def __init__(self):
        self.orig_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1086)
        socket.socket = socks.socksocket
        logger = logging.getLogger("StreamLogger")
        logger.warning("Set proxy to 127.0.0.1:1086")

    def restore(self):
        socket.socket = self.orig_socket
        logger = logging.getLogger("StreamLogger")
        logger.warning("Restore proxy")


def parse_json(url, debug=False):
    logger = logging.getLogger("StreamLogger")
    logger.info(f"Start parsing: {url}")
    time.sleep(REQ_SLEEP)
    if "github.com" in url:
        res = requests.get(url, headers=get_gh_header(), timeout=REQ_TIMEOUT)
        json_str = res.text
        this_head = res.headers
        ts = int(this_head['X-RateLimit-Reset'])
        utc_tc = datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)
        logger.info(f"RateLimit-Limit {this_head['X-RateLimit-Remaining']}/{this_head['X-RateLimit-Limit']}. Reset at TZ@{LOCAL_TZ} " +
                    utc_tc.astimezone(pytz.timezone(LOCAL_TZ)).strftime('%Y-%m-%d %H:%M:%S')+".")
    else:
        res = requests.get(url, headers=SIMPLE_HEADER, timeout=REQ_TIMEOUT)
        json_str = res.text
    json_data = json.loads(json_str)
    if debug:
        logger.debug(json.dumps(json_data, indent=4))
        _reload = Reload("debug.txt")
        logger.debug(json.dumps(json_data, ensure_ascii=False, indent=4))
        _reload.close()
    logger.info("Finish parse URL.")
    return json_data


def parse_json_pool(url_issue_num, debug=False):
    url, issue_num = url_issue_num
    return parse_json(url, debug), issue_num


class TimeCT:
    def __init__(self):
        self.start = time.time()

    def clear(self):
        self.start = time.time()
        return self.start

    @property
    def passed(self):
        return time.time() - self.start


def save_json(json_obj, json_path):
    with open(json_path, 'w', encoding='utf8') as f:
        print(json.dumps(json_obj, indent=4), file=f)


def load_json(json_path):
    with open(json_path, 'r', encoding='utf8') as f:
        json_obj = json.load(f)
    return json_obj


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner


@singleton
class PrintWarp:
    def __init__(self):
        self.pp = pprint.PrettyPrinter(indent=4, stream=sys.stdout)

    def set_stream(self, stream=sys.stdout):
        self.pp._stream = stream

    def pprint(self, object):
        self.set_stream(sys.stdout)
        self.pp.pprint(object)

    def pformat(self, object):
        return self.pp.pformat(object)


class StringHash:
    def __init__(self, init_list=None):
        """
        :param init_list: over 2 dim initial list
        """
        self.bucket = set()
        if init_list is not None:
            for a_list in init_list:
                self.add(a_list)

    @staticmethod
    def to_string(list_obj):
        return list_obj.__repr__()

    @staticmethod
    def parse(text):
        tmp = eval(text)
        if type(tmp) != list:
            raise Exception("Type is not list")
        return tmp

    def add(self, list_obj):
        self.bucket.add(self.to_string(list_obj))

    def exist(self, list_obj):
        return self.to_string(list_obj) in self.bucket

    def remove(self, list_obj):
        self.bucket.remove(self.to_string(list_obj))

    def clear(self):
        self.bucket.clear()

    def get_in_list(self):
        out = list()
        for item in self.bucket:
            out.append(self.parse(item))
        return out


if __name__ == '__main__':
    print(parse_json('https://api.github.com/users/eveneko'))