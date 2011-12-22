from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from PyQt4.QtCore import *
from volumina.api import *

def qimage2jpg( qimg ):
    buffer = QBuffer()
    buffer.open(QIODevice.ReadWrite)
    qimg.save(buffer, 'JPG')
    data = buffer.data()
    buffer.close()        
    return data

class CatmaidServer( HTTPServer ):
    def __init__( self, server_address, RequestHandlerClass, imagesource ):
        HTTPServer.__init__( self, server_address, RequestHandlerClass )
        self.imagesource = imagesource

class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)            
        self.end_headers()
        
        qimg = self.server.imagesource.request(QRect(0,0, 256, 256)).wait()
        data = qimage2jpg(qimg)
        self.wfile.write(data)

        #self.send_error(404, "File not found: %s" % self.path)

if __name__ == '__main__':
    import numpy
    from volumina.pixelpipeline._testing import OpDataProvider
    from volumina._testing.from_lazyflow import OpDataProvider5D, OpDelay
    from volumina.pixelpipeline.imagesources import RandomImageSource
    from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
    from lazyflow import operators

    import volumina.pixelpipeline.imagepump
    from volumina.slicingtools import SliceProjection

    layerstack = LayerStackModel()

    # file = os.path.split(os.path.abspath(__file__))[0] +"/_testing/5d.npy"
    # print "loading file '%s'" % file

    # g = Graph()
    # op1 = OpDataProvider5D(g, file)
    # op2 = OpDelay(g, 0.000003)
    # op2.inputs["Input"].connect(op1.outputs["Data5D"])
    # source = LazyflowSource(op2.outputs["Output"])
    
    # layerstack.append( GrayscaleLayer( source ) )
    
    # print "...done"


    d = (numpy.random.random((1,256, 256, 16,1)) * 255).astype(numpy.uint8)
    source = ArraySource(d)
    layerstack.append( GrayscaleLayer(source) )

    alongTZC = SliceProjection( abscissa = 1, ordinate = 2, along = [0,3,4] )
    pump = volumina.pixelpipeline.imagepump.ImagePump(layerstack, alongTZC)

    from BaseHTTPServer import HTTPServer
    server = CatmaidServer(('localhost', 8080), GetHandler, RandomImageSource())
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
