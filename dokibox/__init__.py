# -*- coding: utf-8 -*-
"""dokibox -- DDLC-style dialog library made by 99"""

from importlib.metadata import version

__version__ = version("dokibox")

from dokibox.ynbox import ynbox
from dokibox.choicebox import choicebox
from dokibox.msgbox import msgbox
from dokibox.enterbox import enterbox
from dokibox.dialogbox import dialogbox, Avatar, addhistory
from dokibox.diaenterbox import diaenterbox
from dokibox.garbled import garbled
from dokibox.textbox import textbox
from dokibox.cmdbox import cmdbox, closecmdbox
from dokibox.notice import notice
