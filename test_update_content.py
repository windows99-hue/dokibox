# -*- coding: utf-8 -*-
"""Regression tests for dokibox.dialogbox._update_content().

Run directly with:
    python test_update_content.py
"""
import importlib
import sys

import dokibox
from PySide6.QtCore import QTimer


dialogbox_module = importlib.import_module("dokibox.dialogbox")


class ExpectedUpdateError(RuntimeError):
    """Marker exception used to verify that update failures are not swallowed."""


def close_dialog_later(delay_ms=50):
    def close_dialog():
        box = dialogbox_module._get_shared_box()
        if box is not None:
            box._done()

    QTimer.singleShot(delay_ms, close_dialog)


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_window_reuse_and_callback_reset():
    def save_callback():
        pass

    dokibox.dialogbox.save = None
    dokibox.dialogbox.load = None
    dokibox.dialogbox.settings = None

    close_dialog_later()
    dokibox.dialogbox("First dialog", typewriter=False, savecall=save_callback)
    first_box = dialogbox_module._get_shared_box()
    check(first_box is not None, "the first dialog created a shared window")
    check(first_box._savecall is save_callback,
          "the per-call save callback was installed")

    close_dialog_later()
    dokibox.dialogbox("Second dialog", typewriter=False)
    second_box = dialogbox_module._get_shared_box()
    check(second_box is first_box, "the second dialog reused the same window")
    check(second_box._savecall is None, "the previous save callback was cleared")
    check(second_box._loadcall is None, "the previous load callback was cleared")
    check(second_box._settingscall is None,
          "the previous settings callback was cleared")


def test_update_exception_propagates():
    box = dialogbox_module._get_shared_box()
    check(box is not None, "a shared window is available for the exception test")
    original_update = box._update_content

    def broken_update(*args, **kwargs):
        raise ExpectedUpdateError("intentional _update_content failure")

    box._update_content = broken_update
    try:
        try:
            dokibox.dialogbox("Exception propagation test", typewriter=False)
        except ExpectedUpdateError:
            print("PASS: _update_content exception propagated to the caller")
        else:
            raise AssertionError("_update_content exception was swallowed")
    finally:
        box._update_content = original_update


def main():
    dialogbox_module._get_app()
    try:
        test_window_reuse_and_callback_reset()
        test_update_exception_propagates()
    finally:
        dialogbox_module._destroy_box()

    print("All _update_content regression tests passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        dialogbox_module._destroy_box()
        raise
