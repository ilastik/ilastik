# Define a function for each message ilastik should be able to process:
# def myAction(shell, data)

def setViewerPos(shell, data):
    # data is a dict which may contain one entry for each coordinate
    pos5d = []
    for l in 'txyzc':
        if l in data:
            pos5d.append(data[l])
        else:
            pos5d.append(0)
    shell.setAllViewersPosition(pos5d)
        
def connectToServer(shell, data):
    if ('port' in data and 'name' in data and 
        isinstance(data['port'], int) and 
        isinstance(data['name'], basestring)):
        if 'host' in data:
            host = data['host']
        else:
            host = 'localhost'
        name = data['name'].encode('ascii','ignore')
        shell.socketServer.connect(host, data['port'], name)
        shell.newServerConnected(name)
    else:
        raise Exception("Please supply at least server 'name' and 'port' for handshake")

# Link command names to function names
allowedCommands = {'setviewerposition': setViewerPos,
                   'handshake': connectToServer}