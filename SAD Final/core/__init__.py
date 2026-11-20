"""
core package initialization.
Kompatibilitas Python 3.15: Patch untuk Django BaseContext.__copy__
Di Python 3.15, pemanggilan copy(super()) di BaseContext.__copy__ menghasilkan salinan objek super,
bukan salinan objek konteks. Patch ini memastikan template rendering pada test client Django berjalan normal.
"""
import copy
from django.template import context

def _compat_base_context_copy(self):
    cls = self.__class__
    duplicate = cls.__new__(cls)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate

context.BaseContext.__copy__ = _compat_base_context_copy
