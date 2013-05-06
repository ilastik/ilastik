from PyQt4.QtCore import QEvent 
from PyQt4.QtGui import QMouseEvent, QWheelEvent, QKeyEvent, QMoveEvent, QWindowStateChangeEvent, QResizeEvent, QContextMenuEvent, QCloseEvent

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



@register_serializer(QMouseEvent)
def QMouseEvent_to_string(mouseEvent):
    type_name = get_event_type_name( mouseEvent.type() )
    button_str = get_mouse_button_string(mouseEvent.button())
    buttons_str = get_mouse_button_string(mouseEvent.buttons())
    key_str = get_key_modifiers_string(mouseEvent.modifiers())
    return "PyQt4.QtGui.QMouseEvent({}, {}, {}, {}, {})".format( type_name, mouseEvent.pos(), button_str, buttons_str, key_str )

@register_serializer(QWheelEvent)
def QWheelEvent_to_string(wheelEvent):
    buttons_str = get_mouse_button_string(wheelEvent.buttons())
    key_str = get_key_modifiers_string(wheelEvent.modifiers())
    return "PyQt4.QtGui.QWheelEvent({}, {}, {}, {}, {})".format( wheelEvent.pos(), wheelEvent.delta(), buttons_str, key_str, wheelEvent.orientation() )

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
    key_str = get_key_modifiers_string(contextMenuEvent.modifiers())
    return "PyQt4.QtGui.QContextMenuEvent({}, {}, {}, {})".format( int(contextMenuEvent.reason()), contextMenuEvent.pos(), contextMenuEvent.globalPos(), key_str )

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

