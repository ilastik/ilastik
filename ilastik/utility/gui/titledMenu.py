from PyQt4.QtGui import QMenu, QLabel, QWidgetAction


def TitledMenu(titles, padding=5, with_separator=True):
    """

    :param title: the title for menu
    :param padding: the padding defaults to 5 px
    :param with_separator: if true adds a separator
    :return: the QMenu with a title
    """
    menu = QMenu()

    for title in titles:
        label = QLabel(title)
        label.setStyleSheet("padding: {}px; background-color: rgba(0, 0, 0, 0);".format(padding))
        title_widget = QWidgetAction(menu)
        title_widget.setDefaultWidget(label)
        menu.addAction(title_widget)

    if with_separator:
        menu.addSeparator()

    return menu