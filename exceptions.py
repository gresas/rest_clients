class ApiRestException(Exception):
    def __init__(self, *args, **kwargs):
        self.status = kwargs.get('status')
        super().__init__(*args)


class MissingConfigurationException(ValueError):
    pass
