"""MyPy strict-mode test file.

Each function below is designed to trigger a specific mypy rule so we can
confirm the configuration catches it. Expected errors are noted inline.
"""

from __future__ import annotations

import functools
from typing import Any, cast


# ── 1. disallow_untyped_defs ──────────────────────────────────────────────────
# Error: Function is missing a type annotation
def no_annotations(x, y):  # noqa: ANN001 ANN201
    return x + y


# ── 2. disallow_incomplete_defs ───────────────────────────────────────────────
# Error: Function is missing annotation for argument "y"
def partial_annotations(x: int, y) -> int:  # noqa: ANN001
    return x + y


# ── 3. disallow_any_generics ──────────────────────────────────────────────────
# Error: Missing type parameters for generic type "list"
def takes_bare_list(items: list) -> None:
    for item in items:
        print(item)


# ── 4. warn_return_any ────────────────────────────────────────────────────────
# Error: Returning Any from function declared to return "int"
def get_any() -> Any:
    return 42


def typed_returns_any() -> int:
    val: Any = get_any()
    return val  # returns Any into int


# ── 5. strict_optional ────────────────────────────────────────────────────────
# Error: Argument 1 to "+" has incompatible type "str | None"
def maybe_name() -> str | None:
    return "Alice"


def greet() -> str:
    name = maybe_name()
    return "Hello, " + name  # name could be None


# ── 6. disallow_untyped_calls ─────────────────────────────────────────────────
# Error: Call to untyped function "no_annotations" in typed context
def calls_untyped() -> int:
    return no_annotations(1, 2)


# ── 7. arg-type ───────────────────────────────────────────────────────────────
# Error: Argument 1 has incompatible type "str"; expected "int"
def add(x: int, y: int) -> int:
    return x + y


wrong_call = add("oops", 1)


# ── 8. warn_unreachable ───────────────────────────────────────────────────────
# Error: Statement is unreachable
def early_return() -> int:
    return 1
    print("dead code")  # noqa: RET504 — intentional for mypy test  # type: ignore[unreachable]


# ── 9. strict_equality ────────────────────────────────────────────────────────
# Error: Non-overlapping equality check (str vs int will never be equal)
def check_overlap(x: int) -> bool:
    return x == "hello"


# ── 10. warn_redundant_casts ──────────────────────────────────────────────────
# Error: Redundant cast to "int"
already_int: int = 42
redundant = cast(int, already_int)


# ── 11. disallow_untyped_decorators ──────────────────────────────────────────
# Error: Untyped decorator makes "decorated_fn" untyped
def untyped_decorator(func):  # noqa: ANN001 ANN201
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


@untyped_decorator
def decorated_fn() -> int:
    return 1


def main() -> None:
    print("MyPy strict-mode test — see inline errors above")


if __name__ == "__main__":
    main()
