# -*- coding: utf-8 -*-
try:
    from unittest import mock
except ImportError:
    import mock


class MockFulfil(object):
    """
    A Mock object that helps mock away the Fulfil API
    for testing.
    """
    responses = []
    models = {}
    context = {}
    subdomain = 'mock-test'

    def __init__(self, target, responses=None):
        self.target = target
        self.reset_mocks()
        if responses:
            self.responses.extend(responses)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()
        self.reset_mocks()
        return type is None

    def model(self, model_name):
        return self.models.setdefault(
            model_name, mock.MagicMock(name=model_name)
        )

    def start(self):
        """
        Start the patch
        """
        self._patcher = mock.patch(target=self.target)
        MockClient = self._patcher.start()
        instance = MockClient.return_value
        instance.model.side_effect = mock.Mock(
            side_effect=self.model
        )

    def stop(self):
        """
        End the patch
        """
        self._patcher.stop()

    def reset_mocks(self):
        """
        Reset all the mocks
        """
        self.models = {}
        self.context = {}
