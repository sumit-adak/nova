"""Tests for memory manager."""

def test_remember_and_recall(memory_manager):
    assert memory_manager.remember("preferred_name", "Sumit")
    assert memory_manager.recall("preferred_name") == "Sumit"


def test_forbidden_keys(memory_manager):
    assert not memory_manager.remember("api_key", "secret123")
    assert memory_manager.recall("api_key") is None


def test_forget(memory_manager):
    memory_manager.remember("theme", "dark")
    assert memory_manager.forget("theme")
    assert memory_manager.recall("theme") is None


def test_clear_all(memory_manager):
    memory_manager.remember("a", "1")
    memory_manager.remember("b", "2")
    count = memory_manager.clear_all()
    assert count >= 2
    assert memory_manager.get_all() == []
