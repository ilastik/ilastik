from ilastikshell.applet import Applet

from opFeatureSelection import OpFeatureSelection

from featureSelectionSerializer import FeatureSelectionSerializer, Ilastik05FeatureSelectionDeserializer
from featureSelectionGui import FeatureSelectionGui

from lazyflow.graph import OperatorWrapper

from utility import OperatorWrapperAdapter

class FeatureSelectionApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, graph ):
        super(FeatureSelectionApplet, self).__init__("Feature Selection")
        
        # Create a data selection top-level operator on the main graph
        # This operator object represents the "model" or master state of the applet which 
        #  the other components of the applet will manipulate and/or listen to for changes.
        self._topLevelOperator = OperatorWrapper( OpFeatureSelection(graph) )

        # Serialization settings are managed by a 
        self._serializableItems = [ FeatureSelectionSerializer(self._topLevelOperator),
                                    Ilastik05FeatureSelectionDeserializer(self._topLevelOperator) ]

        # Instantiate the main GUI, which creates the applet drawers (for now)
        self._centralWidget = FeatureSelectionGui()

        # To save some typing, the menu bar is defined in the .ui file 
        #  along with the rest of the central widget.
        # However, we must expose it here as an applet property since we 
        #  want it to show up properly in the shell
        self._menuWidget = self._centralWidget.menuBar
        
        # The central widget owns the applet drawer gui
        self._drawers = [ ("Feature Selection", self._centralWidget.drawer) ]
        
        # No preferences for this applet (yet)
        self._preferencesManager = None
    
    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def appletDrawers(self):
        return self._drawers
    
    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
         return self._preferencesManager

    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget
    
    def setImageIndex(self, imageIndex):
        """
        Change the currently displayed image to the one specified by the given index.
        """
        if imageIndex is -1 or imageIndex > len(self._topLevelOperator.InputImage):
            newMainOperator = None
        else:
            newMainOperator = OperatorWrapperAdapter( self._topLevelOperator, imageIndex )

        self._centralWidget.setMainOperator( newMainOperator )

