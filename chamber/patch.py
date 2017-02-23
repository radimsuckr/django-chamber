from __future__ import unicode_literals

import six

from django.db.models import Model
from django.db.models.fields import Field


class OptionsLazy(object):

    def __init__(self, name, klass):
        self.name = name
        self.klass = klass

    def __get__(self, instance=None, owner=None):
        return self.klass(owner)


class OptionsBase(type):
    def __new__(cls, *args, **kwargs):
        new_class = super(OptionsBase, cls).__new__(cls, *args, **kwargs)
        if new_class.model_class and new_class.meta_name:
            setattr(new_class.model_class, new_class.meta_name, OptionsLazy(new_class.meta_name, new_class))
        return new_class


class Options(six.with_metaclass(OptionsBase, object)):

    meta_class_name = None
    meta_name = None
    attributes = None
    model_class = None

    def __init__(self, model):
        self.model = model

        for key, default_value in self._get_attributes(model).items():
            setattr(self, key, self._getattr(key, default_value))

    def _get_attributes(self, model):
        return self.attributes

    def _getattr(self, name, default_value):
        meta_models = [b for b in self.model.__mro__ if issubclass(b, Model)]
        for model in meta_models:
            meta = getattr(model, self.meta_class_name, None)
            if meta:
                value = getattr(meta, name, None)
                if value is not None:
                    return value
        return default_value


def field_init(self, *args, **kwargs):
    """
    Patches a Django Field's `__init__` method for easier usage of optional `kwargs`. It defines a `humanized` attribute
    on a field for better display of its value.
    """
    humanize_func = kwargs.pop('humanized', None)
    if humanize_func:
        def humanize(val, inst, *args, **kwargs):
            return humanize_func(val, inst, field=self, *args, **kwargs)
        self.humanized = humanize
    else:
        self.humanized = self.default_humanized
    getattr(self, '_init_chamber_patch_')(*args, **kwargs)


Field.default_humanized = None
Field._init_chamber_patch_ = Field.__init__  # pylint: disable=W0212
Field.__init__ = field_init
