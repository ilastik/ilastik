class IlastikShell( object ):
    def __init__( self ):
        self.main_widget = None
        self.status_bar = None


### Applet = Pipeline + PipelineGui ###

class PipelineGui( object ):
    def __init__( self, pipeline, resource ):
        self.applet_stack = []
    
    def get_main_widget( self ):
        return None

    def get_status_bar( self ):
        return None

class Pipeline( object ):
    def __init__( self ):
        self.opA = None
        self.opB = None

####


p1 = Pipeline()
p2 = Pipeline()

''' wire up p1 and p2 as a workflow here '''
workflow = None

resource = None

# make two applet guis; they share a common gui resource like a volumeeditor
p1Gui = PipelineGui( p1, resource )
p2Gui = PipelineGui( p2, resource )

shell = IlastikShell()
shell.applet_stack.append(p1Gui)
shell.applet_stack.append(p2Gui)


