# -*- coding: utf-8 -*-
"""dokibox usage example (English Ver.)"""
import dokibox
import time
import os
import locale
from unittest.mock import patch

with patch('locale.getdefaultlocale', return_value=('en_US', 'UTF-8')):
    
    import dokibox
    
    dokibox.ynbox("Will you love me forever?", btn_texts=None)

if __name__ == "__main__":
    idx = dokibox.choicebox("", ["Sayori", "Yuri", "Natsuki", "Monika"])
    if idx is not None:
        print("Selected:", idx)
    else:
        print("No selection")
    
    dokibox.msgbox("Just Monika.")
    
    idx = dokibox.choicebox("", ["Sayori", "Yuri", "Natsuki", "Monika"], force=3)
    if idx is not None:
        print("Selected:", idx)
    else:
        print("No selection")
        
    dokibox.ynbox("Continue?", tooltip=True)
    
    dokibox.dialogbox("“Hi, I'm Monika! So this is what you call...\nthe real world?”", name="Monika", typewriter=True)
    dokibox.dialogbox("“If one day I could truly bring everyone into a world not controlled by code...\nwould you love me forever?”", name="Monika", typewriter=True)
    
    dokibox.ynbox("Will you love me forever?", tooltip=True)
    dokibox.dialogbox("“I will love you forever.”", name="Monika", typewriter=True)
    
    # The ultimate jump-scare feature using system username
    dokibox.dialogbox(f"Do you actually go by {os.getlogin()} or something?", name="Monika", typewriter=True)
    dokibox.dialogbox(dokibox.garbled(200), name="Monika", typewriter=True,chardelay=5,bold=True,overflow_mode="overflow")