from ilastik.utility.commands import *

class CommandProcessor(object):
    def __init__(self, shell):
        self.shell = shell
    
    def execute(self, cmd, data):
        if cmd not in allowedCommands:
            raise Exception("Command '%s' not supported" % cmd)
        # if command is implemented, try to execute it with the received data
        try:            
            allowedCommands[cmd](self.shell, data)
        except Exception, e:
            raise Exception("Executing command '%s' failed: %s" % (cmd, e))