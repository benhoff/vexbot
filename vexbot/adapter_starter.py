
def _get_needed_data(adapter_data: dict):
    needed_data = []
    for k, v in adapter_data:
        if not v:
            needed_data.append(k)

    return needed_data


def _start_service(module):
    pass


class AdapterStart:
    def track_adapter(self, intent, data):
        def result_callback():
            return data['response']
        return result_callback

    def start_adapter(self, adapter, service_name):
        pass
