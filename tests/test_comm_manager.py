from BESTLIB.core.comm import CommManager


class DummyEventManager:
    def __init__(self, sink):
        self.sink = sink
    
    def emit(self, event_type, payload):
        self.sink.append((event_type, payload))


def test_comm_manager_emits_on_event_manager():
    events = []
    class DummyLayout:
        _event_manager = DummyEventManager(events)
        _handlers = {}
    layout = DummyLayout()
    CommManager.register_instance('div-test', layout)
    msg = {'content': {'data': {'type': 'select', 'payload': {'items': []}}}}
    CommManager._handle_message('div-test', msg)
    CommManager.unregister_instance('div-test')
    assert events and events[0][0] == 'select'


def test_comm_manager_legacy_handlers():
    calls = []
    def handler(payload):
        calls.append(payload)
    class LegacyLayout:
        _event_manager = None
        _handlers = {'select': [handler]}
    layout = LegacyLayout()
    CommManager.register_instance('div-legacy', layout)
    msg = {'content': {'data': {'type': 'select', 'payload': {'items': [1]}}}}
    CommManager._handle_message('div-legacy', msg)
    CommManager.unregister_instance('div-legacy')
    assert calls and calls[0]['items'] == [1]

