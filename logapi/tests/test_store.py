import unittest

from logapi.datastore import in_memory_store as store
from logapi.datastore import parser
from logapi.server import api as user_api


class TestStore(unittest.TestCase):

    def test_block(self):
        def left_window(offset):
            def invoke():
                return block.get_entries_from_less_or_equal_offsets(offset)
            return invoke

        def right_window(offset):
            def invoke():
                return block.get_entries_from_more_than_offset(offset)
            return invoke
        # empty block - raise exceptions
        block = store.Block(1)
        self.assertRaises(IndexError, left_window(0))
        self.assertRaises(IndexError, right_window(0))

        # partially full bloc
        block.add_entry(100, "a")

        self.assertEqual(1, len(left_window(0)()))
        self.assertEqual(1, len(right_window(0)()))

        # small and full block, window sizes exceed block length
        block = store.Block(1, 2)
        block.add_entry(100, "a")
        block.add_entry(101, "b")
        self.assertEqual(2, len(left_window(1)()))
        self.assertEqual(2, len(right_window(0)()))

    def test_store(self):
        uid1 = 1

        def make_user_generator(size):
            def entries_gen():
                for i in range(size):
                    yield {store.UID: uid1, store.TS: i, store.ENTRY: f"/abc/ + {i}"}
            return entries_gen

        # single block
        memstore = store.InMemoryStore(2)
        memstore.load_log(make_user_generator(2))
        self.assertEqual(
            2, len(memstore.get_user_log_entries_in_window(uid1, 0, 4, 4)))

        # multi block
        memstore = store.InMemoryStore(2)
        memstore.load_log(make_user_generator(10))

        self.assertEqual(
            4, len(memstore.get_user_log_entries_in_window(uid1, 0, 4, 4)))

    def test_parser(self):
        self.assertEqual(
            100, len(list(parser.parse("./data/events-sample.json")())))


if __name__ == '__main__':
    unittest.main()
