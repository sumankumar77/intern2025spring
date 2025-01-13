import logging
from io import StringIO
from django.test import SimpleTestCase

from .constants import PRD_INFO
from .utils import get_model_params


class LoggingTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.stream = StringIO()
        self.logger = logging.getLogger('chealth')
        self.handler = logging.StreamHandler(self.stream)
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        super().tearDown()
        self.stream.close()

    def test_log_level(self):
        with self.assertLogs('chealth', 'ERROR') as cm:
            self.logger.log(PRD_INFO, 'PRD_INFO message')
        self.assertEqual(cm.output, ['PRD_INFO:chealth:PRD_INFO message'])

        with self.assertLogs('chealth', 'CRITICAL') as cm:
            self.logger.log(PRD_INFO, 'PRD_INFO message')
            self.logger.critical('CRITICAL message')
        self.assertEqual(cm.output, ['CRITICAL:chealth:CRITICAL message'])


class UtilsTestCase(SimpleTestCase):
    def test_get_model_params(self):
        data = {'s_attr_1': 19, 's_attr_2': 'char1',
                's_attr_3': {'s_attr_3a': 28, 's_attr_3b': 'char2'}}
        attrs = {'s_attr_1': 't_attr_1', 's_attr_2': 't_attr_2',
                 's_attr_3': {'s_attr_3a': 't_attr_3a', 's_attr_3b': 't_attr_3b'},
                 's_attr_4': 't_attr_4', 's_attr_5': 't_attr_5'}
        char_fields = ['t_attr_2', 't_attr_3b', 't_attr_5']
        params = get_model_params(data, attrs, char_fields=char_fields)
        model_params = {'t_attr_1': 19, 't_attr_2': 'char1',
                        't_attr_3a': 28, 't_attr_3b': 'char2',
                        't_attr_4': None, 't_attr_5': ''}
        self.assertDictEqual(params, model_params)
