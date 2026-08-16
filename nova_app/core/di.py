"""Dependency Injection container for NOVA."""
from typing import Any, Callable, Type, TypeVar

T = TypeVar("T")


class Container:
    """Lightweight thread-safe and async-aware Dependency Injection Container."""

    def __init__(self):
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable[['Container'], Any]] = {}
        self._instances: dict[type, Any] = {}

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a pre-constructed singleton instance."""
        self._singletons[service_type] = instance
        self._instances[service_type] = instance

    def register_factory(self, service_type: Type[T], factory: Callable[['Container'], T]) -> None:
        """Register a factory that constructs an instance when resolved."""
        self._factories[service_type] = factory

    def register_lazy_singleton(self, service_type: Type[T], factory: Callable[['Container'], T]) -> None:
        """Register a factory that is evaluated once and cached as a singleton."""
        self._factories[service_type] = factory

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve an instance for the requested type."""
        if service_type in self._instances:
            return self._instances[service_type]

        if service_type in self._factories:
            instance = self._factories[service_type](self)
            self._instances[service_type] = instance
            return instance

        raise KeyError(f"Service '{service_type.__name__}' is not registered in the DI container.")

    def has(self, service_type: Type[Any]) -> bool:
        """Check if a service type is registered."""
        return service_type in self._instances or service_type in self._factories or service_type in self._singletons

    def clear(self) -> None:
        """Clear all registered services and instances."""
        self._singletons.clear()
        self._factories.clear()
        self._instances.clear()


# Global default container instance
_global_container = Container()


def get_container() -> Container:
    """Return the global DI container."""
    return _global_container
