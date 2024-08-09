"""
Test cast_class in tagulous.models.tagged
"""

import inspect
import pickle

from pytest import fixture

from tagulous.models.cast import cast_instance, get_cast_class
from tests.tagulous_tests_app.cast import NewBase, OldBase, Target

EXPECTED_CAST_NAME = "TagulousCastTaggedTarget"


@fixture
def Cast():
    # Create a class for use during tests and remove it from the module afterwards
    cls = get_cast_class(Target, NewBase)
    yield cls
    delattr(inspect.getmodule(Target), cls.__name__)


@fixture
def instance():
    v = 1
    obj = Target(v)
    cast_instance(obj, NewBase)
    yield obj
    delattr(inspect.getmodule(Target), obj.__class__.__name__)


def test_get_cast_class__name(Cast):
    assert Cast.__name__ == EXPECTED_CAST_NAME


def test_get_cast_class__mro(Cast):
    assert Cast.__bases__ == (NewBase, Target)
    assert Cast.__bases__[0].__bases__ == (object,)
    assert Cast.__bases__[1].__bases__ == (OldBase,)


def test_get_cast_class__existing_found(Cast):
    first_id = id(Cast)
    ReCast = get_cast_class(Target, NewBase)
    second_id = id(ReCast)
    assert first_id == second_id


def test_get_cast_class__module(Cast):
    orig_module = inspect.getmodule(Target)
    cast_module = inspect.getmodule(Cast)
    assert orig_module == cast_module


def test_get_cast_class__pickle(Cast):
    v = 1
    obj = Cast(v)
    pickled = pickle.dumps(obj)
    unpickled = pickle.loads(pickled)
    assert unpickled.v == v


def test_cast_instance__class_name(instance):
    assert instance.__class__.__name__ == EXPECTED_CAST_NAME


def test_cast_instance__mro(instance):
    assert instance.__class__.__bases__ == (NewBase, Target)
    assert instance.__class__.__bases__[0].__bases__ == (object,)
    assert instance.__class__.__bases__[1].__bases__ == (OldBase,)


def test_cast_instance__value_unchanged(instance):
    assert instance.v == 1
