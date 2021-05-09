
from logapi.datastore import in_memory_store as store


def events_response(events=[]):
    return {store.EVENTS: events}


class AccessLogApi:
    """
    API emulating Flask,returing a python dictionary whicg Flask trandform to JSON

    TBD insead 'offset' work with event id with possible format such as f'{uid}-{offset}'
    """

    def __init__(self, store):
        self.store = store

    # /user/events/{uid}
    def user_events(self, uid):
        """
            Return window of latest events
            TBD accept time range and return latest as default
        """
        offset = self.store.find_latest_user_entry_offset(uid)
        if offset == -1:
            return events_response()
        events = self.store.get_user_log_entries_in_window(
            uid, offset, 2*store.LEFT_WINDOW_SIZE, 0)
        return events_response(events)

    # /user_events_in_window/{uid}/{offset}
    def user_events_in_window(self, uid, offset):
        events = self.get_user_log_entries_in_window(uid, offset)
        return events_response(events)

    # /next_user_events/{uid}/{right_offset}
    def next_user_events(self, uid, right_offset):
        events = self.store.get_user_log_entries_in_window(
            uid, right_offset, 0, store.RIGHT_WINDOW_SIZE, False)
        return events_response(events)

    # /previous_user_events/{uid}/{left_offset}
    def previous_user_events(self, uid, left_offset):
        events = self.store.get_user_log_entries_in_window(
            uid, left_offset, store.LEFT_WINDOW_SIZE, 0, False)
        return events_response(events)
