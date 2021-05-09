import unittest
import pprint
import json

from logapi.datastore import in_memory_store as store
from logapi.datastore import parser
from logapi.server import api as user_api


def print_events(uid, events, msg):
    print(f"user: {uid} events  {msg}")
    for i in events[store.EVENTS]:
        print(
            f"{i[store.TS]} ({i[store.OFFSET]}) {i[store.ENTRY][store.METHOD]} {i[store.ENTRY][store.URL]}")


class TestStore(unittest.TestCase):

    def test_api(self):
        memstore = store.InMemoryStore()
        parser_gen = parser.parse("./data/events-sample.json")
        memstore.load_log(parser_gen)
        api = user_api.AccessLogApi(memstore)
        memstore = store.InMemoryStore()
        memstore.load_log(parser_gen)
        api = user_api.AccessLogApi(memstore)
        uid = "31b20726-b870-47ba-bbcd-372b38527c89"
        events = api.user_events(uid)
        print_events(uid, events, "latest events")
        offset = events[store.EVENTS][-1][store.OFFSET]
        # save to compare with previous events
        one_before_last_offset = events[store.EVENTS][-2][store.OFFSET]
        events = api.next_user_events(uid, offset)
        # no more events beyond last
        self.assertEqual(0, len(events[store.EVENTS]))
        events = api.previous_user_events(uid, offset)
        print_events(uid, events, "scroll backwards excluding last")
        self.assertEqual(events[store.EVENTS][-1][store.OFFSET],
                         one_before_last_offset)  # last event
        first_offset = events[store.EVENTS][0][store.OFFSET]
        events = api.next_user_events(uid, first_offset)
        print_events(uid, events, "scroll forwards excluding first")
        self.assertEqual(events[store.EVENTS][-1][store.OFFSET],
                         offset)  # got to same location as beginning


if __name__ == '__main__':
    unittest.main()
