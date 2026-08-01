import dokibox

def save2():
    dokibox.msgbox("保存2")

def save():
    dokibox.msgbox("保存")

dokibox.dialogbox.save = None

dokibox.dialogbox("hi", savecall=save2)
dokibox.dialogbox("hi2",fdst=True)

# Regression check: the command should finish typing before execution starts.
# During the five-second execution, the cursor and window should keep updating;
# captured output should appear only after execution finishes.
# blocking_command = (
#     "import time\n"
#     "print('Command started')\n"
#     "time.sleep(5)\n"
#     "print('Command finished')"
# )

blocking_command = (
    "import time\n"
    "print('Command started')\n"
    "for i in range(5):\n"
    "    time.sleep(1)\n"
    "    print(f'Elapsed time: {i+1} seconds')\n"
    "print('Command finished')"
)

dokibox.cmdbox(
    blocking_command,
    runcmd=True,
    language="python",
    clear=True,
    chardelay=30,
)
dokibox.closecmdbox(delay=3000)
dokibox.dialogbox("Command execution finished. Check the output above.", name="System", typewriter=True)