from logapi.datastore import *


class Block:
    """ Block represents single user ordered entries from the  source access log"""

    def __init__(self, uid, max_size=MAX_BLOCK_SIZE):
        super().__init__()
        self.uid = uid
        self._timestamps = []
        self._entries = []
        self._max_size = max_size

    def add_entry(self, ts, entry):
        if len(self._timestamps) == self._max_size:
            raise BufferError("exceeding block size")
        if self._timestamps and ts < self._timestamps[-1]:
            raise ValueError("out of order entry")
        self._timestamps.append(ts)
        self._entries.append(entry)

    def transform(self, offset):
        return {
            OFFSET: offset,
            UID: self.uid,
            TS: self._timestamps[offset],
            ENTRY: self._entries[offset]
        }

    def get_entries_from_less_or_equal_offsets(self, offset, max_window_size=LEFT_WINDOW_SIZE, include_anchor=True):
        if offset >= self.size:
            raise IndexError("offset exceeding block size")
        anchor_offset = 1 if include_anchor else 0
        left = max(0, offset - max_window_size - anchor_offset)
        return [self.transform(i) for i in range(left, offset + anchor_offset)]

    def get_entries_from_more_than_offset(self, offset, max_window_size=RIGHT_WINDOW_SIZE):
        if offset >= self.size:
            raise IndexError("offset exceeding block size")
        right = min(self.size, offset + max_window_size)
        return [self.transform(i) for i in range(offset, right)]

    @property
    def size(self):
        return len(self._timestamps)


class InMemoryStore:
    """
        InMemoryStore -  holds access log enties in memory
        Internal representation:
        log:
            -user:
                blocks:[]
    """

    def __init__(self, max_block_size=MAX_BLOCK_SIZE):
        self._log = {}
        self._max_block_size = max_block_size

    def load_log(self, entries_gen):
        for e in entries_gen():
            uid = e[UID]
            blocks = self._log.setdefault(
                uid, [Block(uid, self._max_block_size)])
            block = blocks[-1]
            if block.size == self._max_block_size:
                block = Block(uid, self._max_block_size)
                self._log[uid].append(block)
            block.add_entry(e[TS], e[ENTRY])

    def get_user_log_entries_in_window(self, uid, offset, left_window_size=LEFT_WINDOW_SIZE,
                                       right_window_size=RIGHT_WINDOW_SIZE, include_anchor=True):
        if left_window_size > 2 * self._max_block_size or right_window_size > 2 * self._max_block_size:
            raise ValueError("window is too large")
        requested_offset = offset
        if uid not in self._log:
            return []  # not an error - user might not have entries yet
        block_index = offset // self._max_block_size
        if block_index < 0 or block_index >= len(self._log[uid]):
            raise ValueError("Offset is out of range")
        offset -= block_index * self._max_block_size
        block = self._log[uid][block_index]
        if offset >= block.size:
            raise ValueError("Offset is out of range")
        # Left window side
        entries = block.get_entries_from_less_or_equal_offsets(
            offset, left_window_size, include_anchor)
        self._add_block_offset(entries, block_index)
        anchor_offset = 1 if include_anchor else 0
        if len(entries) < left_window_size + anchor_offset and block_index > 0:
            # Left overflow
            remaining = left_window_size - len(entries)
            offset_in_block = self._max_block_size - remaining
            remaining_entries = self._log[uid][block_index - 1] \
                .get_entries_from_less_or_equal_offsets(
                    offset_in_block,
                    remaining)  # anchor is included with first block
            self._add_block_offset(remaining_entries, block_index - 1)
            entries = remaining_entries + remaining_entries
        # Right window side
        offset += 1
        if offset >= self._max_block_size:
            offset = 0
            block_index += 1
            block = self._log[uid][block_index] if block_index < len(
                self._log[uid]) else None
        if block and offset < block.size:
            # Right overflow
            right_entries = block.get_entries_from_more_than_offset(
                offset, right_window_size)
            self._add_block_offset(right_entries, block_index)
            if len(right_entries) < right_window_size and block_index < len(self._log[uid]) - 1:
                remaining = right_window_size - len(right_entries)
                remaining_entries = self._log[uid][block_index + 1].get_entries_from_more_than_offset(
                    0, remaining)
                self._add_block_offset(remaining_entries, block_index + 1)
                right_entries += remaining_entries
            entries += right_entries
        return entries

    def find_latest_user_entry_offset(self, uid):
        """ return -1 if no entries found """
        if uid not in self._log:
            return -1  # not an error - user might not have entries yet
        offset = max(0, (len(self._log[uid]) - 1)) * \
            self._max_block_size + self._log[uid][-1].size - 1
        return offset

    def _add_block_offset(self, entries, block_index):
        for e in entries:
            e[OFFSET] += block_index * self._max_block_size
