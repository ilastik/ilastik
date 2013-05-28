from PyQt4.QtCore import QEvent, QPoint
from PyQt4.QtGui import QMouseEvent, QWheelEvent, QKeyEvent, QMoveEvent, QWindowStateChangeEvent, \
                        QResizeEvent, QContextMenuEvent, QCloseEvent, QApplication

from eventTypeNames import get_event_type_name, get_mouse_button_string, get_key_modifiers_string

event_serializers = {}

def register_serializer(eventType):
    def _dec(f):
        event_serializers[eventType] = f
        return f
    return _dec

def event_to_string(e):
    """
    Convert the given event into a string that can be eval'd in Python.
    """
    return event_serializers[type(e)](e)

##
## Note: Some events use 'global' coordinates, which are global to the screen (not the main window).
##       We serialize the coordinates relative to the shell's corner window, 
##        and then calculate the global coordinates from the relative ones during playback.
##       This allows us to not worry about moving the main window around the screen while we're recording test cases.
##

@register_serializer(QMouseEvent)
def QMouseEvent_to_string(mouseEvent):
    from ilastik.shell.gui.startShellGui import shell   
    type_name = get_event_type_name( mouseEvent.type() )
    button_str = get_mouse_button_string(mouseEvent.button())
    buttons_str = get_mouse_button_string(mouseEvent.buttons())
    key_str = get_key_modifiers_string(mouseEvent.modifiers())
    topLeftCorner_global = shell.mapToGlobal( QPoint(0,0) )
    relPos = mouseEvent.globalPos() - topLeftCorner_global
    return "PyQt4.QtGui.QMouseEvent({}, {}, shell.mapToGlobal( QPoint(0,0) ) + {}, {}, {}, {})".format( type_name, mouseEvent.pos(), relPos, button_str, buttons_str, key_str )

@register_serializer(QWheelEvent)
def QWheelEvent_to_string(wheelEvent):
    from ilastik.shell.gui.startShellGui import shell   
    buttons_str = get_mouse_button_string(wheelEvent.buttons())
    key_str = get_key_modifiers_string(wheelEvent.modifiers())
    topLeftCorner_global = shell.mapToGlobal( QPoint(0,0) )
    relPos = wheelEvent.globalPos() - topLeftCorner_global
    return "PyQt4.QtGui.QWheelEvent({}, shell.mapToGlobal( QPoint(0,0) ) + {}, {}, {}, {}, {})".format( wheelEvent.pos(), relPos, wheelEvent.delta(), buttons_str, key_str, wheelEvent.orientation() )

@register_serializer(QKeyEvent)
def QKeyEvent_to_string(keyEvent):
    text = str(keyEvent.text())
    text = text.replace('\n', '\\n')
    text = text.replace('"', '\\"')
    text = text.replace("'", "\\'")
    text = '"""' + text + '"""'
    type_name = get_event_type_name( keyEvent.type() )
    mod_str = get_key_modifiers_string(keyEvent.modifiers())
    return "PyQt4.QtGui.QKeyEvent({}, 0x{:x}, {}, {}, {}, {})".format( type_name, keyEvent.key(), mod_str, text, keyEvent.isAutoRepeat(), keyEvent.count() )

@register_serializer(QMoveEvent)
def QMoveEvent_to_string(moveEvent):
    return "PyQt4.QtGui.QMoveEvent({}, {})".format( moveEvent.pos(), moveEvent.oldPos() )

@register_serializer(QContextMenuEvent)
def QContextMenuEvent_to_string(contextMenuEvent):
    from ilastik.shell.gui.startShellGui import shell   
    key_str = get_key_modifiers_string(contextMenuEvent.modifiers())
    topLeftCorner_global = shell.mapToGlobal( QPoint(0,0) )
    relPos = contextMenuEvent.globalPos() - topLeftCorner_global
    return "PyQt4.QtGui.QContextMenuEvent({}, {}, shell.mapToGlobal( QPoint(0,0) ) + {}, {})".format( int(contextMenuEvent.reason()), contextMenuEvent.pos(), relPos, key_str )

@register_serializer(QResizeEvent)
def QResizeEvent_to_string(resizeEvent):
    return "PyQt4.QtGui.QResizeEvent({}, {})".format( resizeEvent.size(), resizeEvent.oldSize() )

@register_serializer(QWindowStateChangeEvent)
def QWindowStateChangeEvent_to_string(windowStateChangeEvent):
    return "PyQt4.QtGui.QWindowStateChangeEvent(0x{:x})".format( int(windowStateChangeEvent.oldState()) )

@register_serializer(QCloseEvent)
def QCloseEvent_to_string(closeEvent):
    return "PyQt4.QtGui.QCloseEvent()"

@register_serializer(QEvent)
def QEvent_to_string(event):
    type_name = get_event_type_name( event.type() )
    # Some event types are not exposed in pyqt as symbols
    if not hasattr( QEvent, type_name ):
        type_name = int(event.type())
    return "PyQt4.QtCore.QEvent({})".format( type_name )

