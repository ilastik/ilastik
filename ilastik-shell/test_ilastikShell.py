import unittest as ut
from PyQt4.QtGui import QApplication

from ilastikShell import IlastikShell
from applet import Applet

class IlastikShellTest( ut.TestCase ):
    def setUp( self ):
        self.qapp = QApplication([])

    def test_addApplet( self ):
        shell = IlastikShell()
        applet = Applet()
        self.assertEqual(len(shell), 0)
        index = shell.addApplet(applet)
        self.assertEqual(shell[index],applet) 
        self.assertEqual(len(shell), 1)        

    def test_currentIndex( self ):
        shell = IlastikShell()
        self.assertEqual(shell.currentIndex(), -1 )
        shell.addApplet(Applet())
        self.assertEqual(shell.currentIndex(), 0 )
        shell.addApplet(Applet())
        self.assertEqual(shell.currentIndex(), 0 )
        shell.setCurrentIndex( 1 )
        self.assertEqual(shell.currentIndex(), 1 )

    def test_indexOf( self ):
        shell = IlastikShell()
        a1 = Applet()
        a2 = Applet()
        i1 = shell.addApplet(a1)
        i2 = shell.addApplet(a2)
        self.assertEqual(shell.indexOf(a1), i1)
        self.assertEqual(shell.indexOf(a2), i2)        

    def test_setCurrentIndex( self ):
        shell = IlastikShell()
        i1 = shell.addApplet(Applet())
        i2 = shell.addApplet(Applet())
        shell.setCurrentIndex(i2)
        self.assertEqual(shell.currentIndex(), i2)
        shell.setCurrentIndex(i1)
        self.assertEqual(shell.currentIndex(), i1)

    def test___len__( self ):
        shell = IlastikShell()
        self.assertEqual(len(shell), 0)
        shell.addApplet(Applet())
        shell.addApplet(Applet())        
        self.assertEqual(len(shell), 2)

    def test___getitem__( self ):
        shell = IlastikShell()
        a1 = Applet()
        a2 = Applet()
        i1 = shell.addApplet(a1)
        i2 = shell.addApplet(a2)
        self.assertEqual(shell[i1], a1)
        self.assertEqual(shell[i2], a2)        



if __name__ == "__main__":
    ut.main()


