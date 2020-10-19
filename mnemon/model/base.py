"""Abstract classes for defining the domain model"""

from abc import (
    ABCMeta,  # @UnusedImport
    )


class Entity(metaclass=ABCMeta):
    """Base abstract class for all entities"""


class ValueObject(metaclass=ABCMeta):
    """Base abstract class for all value objects"""


class Repository(metaclass=ABCMeta):
    """Base abstract class for all repositories"""


class Service(metaclass=ABCMeta):
    """Base abstract class for all services"""
