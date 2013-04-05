
def get_event_type_name( event_type ):
    return EventTypeNameDict[event_type]

def get_mouse_button_string(buttons):
    buttonNames = [ ('Qt.LeftButton',   0x00000001),
                    ('Qt.RightButton',  0x00000002),
                    ('Qt.MiddleButton', 0x00000004),
                    ('Qt.XButton1',     0x00000008),
                    ('Qt.XButton2',     0x00000010) ]

    return _get_flags_string(buttons, 'Qt.NoButton', buttonNames)

def get_key_modifiers_string(modifiers):
    modifierNames = [ ('Qt.ShiftModifier',       0x02000000),
                      ('Qt.ControlModifier',     0x04000000),
                      ('Qt.AltModifier',         0x08000000),
                      ('Qt.MetaModifier',        0x10000000),
                      ('Qt.KeypadModifier',      0x20000000),
                      ('Qt.GroupSwitchModifier', 0x40000000) ]

    return _get_flags_string(modifiers, 'Qt.NoModifier', modifierNames)

def _get_flags_string(flags, defaultName, flagNames):
    flags = int(flags)
    if flags == 0:
        return defaultName

    combinedName = "("
    for name, flag in flagNames:
        if flags & flag != 0:
            combinedName += name
            flags &= ~flag
            if flags != 0:
                combinedName += " | "
    combinedName += ")"
    return combinedName


class _EventTypes(object):
        None_ = 0                               # invalid event
        Timer = 1                              # timer event
        MouseButtonPress = 2                   # mouse button pressed
        MouseButtonRelease = 3                 # mouse button released
        MouseButtonDblClick = 4                # mouse button double click
        MouseMove = 5                          # mouse move
        KeyPress = 6                           # key pressed
        KeyRelease = 7                         # key released
        FocusIn = 8                            # keyboard focus received
        FocusOut = 9                           # keyboard focus lost
        Enter = 10                             # mouse enters widget
        Leave = 11                             # mouse leaves widget
        Paint = 12                             # paint widget
        Move = 13                              # move widget
        Resize = 14                            # resize widget
        Create = 15                            # after widget creation
        Destroy = 16                           # during widget destruction
        Show = 17                              # widget is shown
        Hide = 18                              # widget is hidden
        Close = 19                             # request to close widget
        Quit = 20                              # request to quit application
        ParentChange = 21                      # widget has been reparented
        ParentAboutToChange = 131              # sent just before the parent change is done
##ifdef QT3_SUPPORT
#        Reparent = ParentChange
##endif
        ThreadChange = 22                      # object has changed threads
        WindowActivate = 24                    # window was activated
        WindowDeactivate = 25                  # window was deactivated
        ShowToParent = 26                      # widget is shown to parent
        HideToParent = 27                      # widget is hidden to parent
        Wheel = 31                             # wheel event
        WindowTitleChange = 33                 # window title changed
        WindowIconChange = 34                  # icon changed
        ApplicationWindowIconChange = 35       # application icon changed
        ApplicationFontChange = 36             # application font changed
        ApplicationLayoutDirectionChange = 37  # application layout direction changed
        ApplicationPaletteChange = 38          # application palette changed
        PaletteChange = 39                     # widget palette changed
        Clipboard = 40                         # internal clipboard event
        Speech = 42                            # reserved for speech input
        MetaCall =  43                         # meta call event
        SockAct = 50                           # socket activation
        WinEventAct = 132                      # win event activation
        DeferredDelete = 52                    # deferred delete event
        DragEnter = 60                         # drag moves into widget
        DragMove = 61                          # drag moves in widget
        DragLeave = 62                         # drag leaves or is cancelled
        Drop = 63                              # actual drop
        DragResponse = 64                      # drag accepted/rejected
        ChildAdded = 68                        # new child widget
        ChildPolished = 69                     # polished child widget
##ifdef QT3_SUPPORT
#        ChildInsertedRequest = 67              # send ChildInserted compatibility events to receiver
#        ChildInserted = 70                     # compatibility child inserted
#        LayoutHint = 72                        # compatibility relayout request
##endif
        ChildRemoved = 71                      # deleted child widget
        ShowWindowRequest = 73                 # widget's window should be mapped
        PolishRequest = 74                     # widget should be polished
        Polish = 75                            # widget is polished
        LayoutRequest = 76                     # widget should be relayouted
        UpdateRequest = 77                     # widget should be repainted
        UpdateLater = 78                       # request update() later

        EmbeddingControl = 79                  # ActiveX embedding
        ActivateControl = 80                   # ActiveX activation
        DeactivateControl = 81                 # ActiveX deactivation
        ContextMenu = 82                       # context popup menu
        InputMethod = 83                       # input method
        AccessibilityPrepare = 86              # accessibility information is requested
        TabletMove = 87                        # Wacom tablet event
        LocaleChange = 88                      # the system locale changed
        LanguageChange = 89                    # the application language changed
        LayoutDirectionChange = 90             # the layout direction changed
        Style = 91                             # internal style event
        TabletPress = 92                       # tablet press
        TabletRelease = 93                     # tablet release
        OkRequest = 94                         # CE (Ok) button pressed
        HelpRequest = 95                       # CE (?)  button pressed

        IconDrag = 96                          # proxy icon dragged

        FontChange = 97                        # font has changed
        EnabledChange = 98                     # enabled state has changed
        ActivationChange = 99                  # window activation has changed
        StyleChange = 100                      # style has changed
        IconTextChange = 101                   # icon text has changed
        ModifiedChange = 102                   # modified state has changed
        MouseTrackingChange = 109              # mouse tracking state has changed

        WindowBlocked = 103                    # window is about to be blocked modally
        WindowUnblocked = 104                  # windows modal blocking has ended
        WindowStateChange = 105

        ToolTip = 110
        WhatsThis = 111
        StatusTip = 112

        ActionChanged = 113
        ActionAdded = 114
        ActionRemoved = 115

        FileOpen = 116                         # file open request

        Shortcut = 117                         # shortcut triggered
        ShortcutOverride = 51                  # shortcut override request

##ifdef QT3_SUPPORT
#        Accel = 30                             # accelerator event
#        AccelAvailable = 32                    # accelerator available event
#        AccelOverride = ShortcutOverride       # accelerator override event
##endif

        WhatsThisClicked = 118

##ifdef QT3_SUPPORT
#        CaptionChange = WindowTitleChange
#        IconChange = WindowIconChange
##endif
        ToolBarChange = 120                    # toolbar visibility toggled

        ApplicationActivate = 121              # application has been changed to active
        ApplicationActivated = ApplicationActivate # deprecated
        ApplicationDeactivate = 122            # application has been changed to inactive
        ApplicationDeactivated = ApplicationDeactivate # deprecated

        QueryWhatsThis = 123                   # query what's this widget help
        EnterWhatsThisMode = 124
        LeaveWhatsThisMode = 125

        ZOrderChange = 126                     # child widget has had its z-order changed

        HoverEnter = 127                       # mouse cursor enters a hover widget
        HoverLeave = 128                       # mouse cursor leaves a hover widget
        HoverMove = 129                        # mouse cursor move inside a hover widget

        AccessibilityHelp = 119                # accessibility help text request
        AccessibilityDescription = 130         # accessibility description text request

        # last event id used = 132

##ifdef QT_KEYPAD_NAVIGATION
#        EnterEditFocus = 150                   # enter edit mode in keypad navigation (Defined only with QT_KEYPAD_NAVIGATION)
#        LeaveEditFocus = 151                   # leave edit mode in keypad navigation (Defined only with QT_KEYPAD_NAVIGATION)
##endif
        AcceptDropsChange = 152

        MenubarUpdated = 153                    # Support event for Q3MainWindow which needs to
                                                 # knwow when QMenubar is updated.

        ZeroTimerEvent = 154                   # Used for Windows Zero timer events

        GraphicsSceneMouseMove = 155           # GraphicsView
        GraphicsSceneMousePress = 156
        GraphicsSceneMouseRelease = 157
        GraphicsSceneMouseDoubleClick = 158
        GraphicsSceneContextMenu = 159
        GraphicsSceneHoverEnter = 160
        GraphicsSceneHoverMove = 161
        GraphicsSceneHoverLeave = 162
        GraphicsSceneHelp = 163
        GraphicsSceneDragEnter = 164
        GraphicsSceneDragMove = 165
        GraphicsSceneDragLeave = 166
        GraphicsSceneDrop = 167
        GraphicsSceneWheel = 168

        KeyboardLayoutChange = 169             # keyboard layout changed

        DynamicPropertyChange = 170            # A dynamic property was changed through setProperty/property

        TabletEnterProximity = 171
        TabletLeaveProximity = 172

        NonClientAreaMouseMove = 173
        NonClientAreaMouseButtonPress = 174
        NonClientAreaMouseButtonRelease = 175
        NonClientAreaMouseButtonDblClick = 176

        MacSizeChange = 177                    # when the Qt::WA_Mac{NormalSmallMini}Size changes

        ContentsRectChange = 178               # sent by QWidget::setContentsMargins (internal)

        MacGLWindowChange = 179                # Internal! the window of the GLWidget has changed

        FutureCallOut = 180

        GraphicsSceneResize  = 181
        GraphicsSceneMove  = 182

        CursorChange = 183
        ToolTipChange = 184

        NetworkReplyUpdated = 185              # Internal for QNetworkReply

        GrabMouse = 186
        UngrabMouse = 187
        GrabKeyboard = 188
        UngrabKeyboard = 189
        MacGLClearDrawable = 191               # Internal Cocoa the window has changed so we must clear

        StateMachineSignal = 192
        StateMachineWrapped = 193

        TouchBegin = 194
        TouchUpdate = 195
        TouchEnd = 196

##ifndef QT_NO_GESTURES
#        NativeGesture = 197                    # Internal for platform gesture support
##endif
        RequestSoftwareInputPanel = 199
        CloseSoftwareInputPanel = 200

        UpdateSoftKeys = 201                   # Internal for compressing soft key updates

        WinIdChange = 203
##ifndef QT_NO_GESTURES
#        Gesture = 198
#        GestureOverride = 202
##endif

        PlatformPanel = 212

        # 512 reserved for Qt Jambi's MetaCall event
        # 513 reserved for Qt Jambi's DeleteOnMainThread event

        User = 1000                            # first user event id
        MaxUser = 65535

EventTypeNameDict = {}
for k,v in _EventTypes.__dict__.items():
    EventTypeNameDict[v] = 'QEvent.' + k
    


            