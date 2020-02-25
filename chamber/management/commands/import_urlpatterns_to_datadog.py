# https://stackoverflow.com/a/39575249
# https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher.find_longest_match
import re
from difflib import SequenceMatcher

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import RegexURLPattern, RegexURLResolver


class Command(BaseCommand):

    _matcher = SequenceMatcher(lambda x: x == ' ', 'abc', 'bc')
    _names = set()
    _patterns = set()
    _regex = re.compile(r'\(\?.*\)')

    def parse_url_patterns(self, url_patterns, prefix=None):
        for item in url_patterns:
            if isinstance(item, RegexURLPattern):
                pattern = item.regex.pattern if not prefix else f'{prefix}{item.regex.pattern}'
                self._patterns.add(pattern)
                self._names.add(item.name)
            if isinstance(item, RegexURLResolver):
                self.parse_url_patterns(item.url_patterns, prefix if prefix is not None else item.regex.pattern)
        return self._patterns

    def post_process_patterns(self, patterns):
        return (self._regex.sub('*', pattern).replace('^', '').replace('$', '') for pattern in patterns)

    def add_arguments(self, parser):
        parser.add_argument(
            '-m', '--module-name',
            default=settings.ROOT_URLCONF,
            dest='module_name',
            help='URLConf module to use',
            type=str,
        )
        parser.add_argument(
            '-p', '--patterns-variable',
            default='urlpatterns',
            dest='patterns_variable',
            help='URL patterns variable name',
            type=str,
        )

    def handle(self, *args, **options):
        module_name = options['module_name']
        urls_module_name = module_name.split('.')[-1]
        patterns_variable = options['patterns_variable']

        module = __import__(module_name)
        urls_module = getattr(module, urls_module_name)
        patterns = getattr(urls_module, patterns_variable)

        processed_patterns = self.post_process_patterns(self.parse_url_patterns(patterns))
        for pattern in processed_patterns:
            print(pattern)
