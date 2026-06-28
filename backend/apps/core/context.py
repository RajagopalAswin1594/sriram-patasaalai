import threading
import uuid
from contextlib import contextmanager

_thread_locals = threading.local()


def get_audit_context():
    return getattr(_thread_locals, "audit_context", {})


def set_audit_context(**kwargs):
    ctx = get_audit_context().copy()
    ctx.update(kwargs)
    _thread_locals.audit_context = ctx


def clear_audit_context():
    _thread_locals.audit_context = {}


@contextmanager
def audit_context(**kwargs):
    previous = get_audit_context().copy()
    set_audit_context(**kwargs)
    try:
        yield
    finally:
        _thread_locals.audit_context = previous


def get_correlation_id():
    ctx = get_audit_context()
    correlation_id = ctx.get("correlation_id")
    if not correlation_id:
        correlation_id = uuid.uuid4()
        set_audit_context(correlation_id=correlation_id)
    return correlation_id
