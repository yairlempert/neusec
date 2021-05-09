import json
import datetime
from logapi.datastore import *

EVENT_ID = "{event_id}"


def parse(filename):
    """ Return sorted by timestamp access log entries generator """
    def parse_gen():
        with open(filename, "r") as fin:
            for line in fin:
                entry_dict = json.loads(line)
                endpoint_path = entry_dict['endpoint_path']
                method = entry_dict['method']
                ts = int(datetime.datetime.strptime(
                    entry_dict['timestamp'], '%Y-%m-%d %H:%M:%S.%f').strftime('%s'))
                uid = entry_dict['user_id']
                if EVENT_ID in endpoint_path:
                    event_id = entry_dict['url'].split('/')[-1]
                    idx = endpoint_path.find(EVENT_ID)
                    endpoint_path = endpoint_path[:idx] + \
                        event_id + endpoint_path[idx + len(EVENT_ID):]
                yield {UID: uid, TS: ts, ENTRY: {
                    "url": endpoint_path,
                    "method": method
                }}

    def entries_gen():
        entries = list(parse_gen())
        entries = sorted(entries, key=lambda a: a[TS])
        for e in entries:
            yield e
    return entries_gen
