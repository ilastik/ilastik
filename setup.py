from setuptools import setup, find_packages
from ilastik import __version__

packages=find_packages(exclude=["tests", "tests.*"])

package_data={'ilastik': ['ilastik-splash.png',
                          'ilastik-splash.xcf'],
          'ilastik.applets.batchIo': ['*.ui'],
          'ilastik.applets.carving': ['*.ui'],
          'ilastik.applets.dataSelection': ['*.ui'],          
          'ilastik.applets.featureSelection': ['*.ui'],
          'ilastik.applets.labeling': ['*.ui', 'icons/*.png', 'icons/*.jpg'],
          'ilastik.applets.layerViewer': ['*.ui'],
          'ilastik.applets.objectClassification': ['*.ui'],
          'ilastik.applets.objectExtraction': ['*.ui'],
          'ilastik.applets.objectExtractionMultiClass': ['*.ui'],
          'ilastik.applets.pixelClassification': ['*.ui'],
          'ilastik.applets.projectMetadata': ['*.ui'],
          'ilastik.applets.stopWatch': ['*.ui'],
          'ilastik.applets.thresholdMasking': ['*.ui'],
          'ilastik.applets.tracking': ['*.ui'],          
          'ilastik.applets.tracking.base': ['*.ui'],
          'ilastik.applets.tracking.chaingraph': ['*.ui'],
          'ilastik.applets.tracking.fastApproximate': ['*.ui'],
          'ilastik.applets.vigraWatershedViewer': ['*.ui'],
          'ilastik.shell.gui': ['ui/*.ui', '*.qss'],
          'ilastik.ilastik_logging': ['logging_config.json'],
          'ilastik.widgets': ['*.ui']
              }
package_data={'ilastik': ['ilastik-splash.png',
                          'ilastik-splash.xcf'],
              'ilastik.applets.labeling': ['*.ui', 'icons/*.png', 'icons/*.jpg'],
              'ilastik.shell.gui': ['ui/*.ui', '*.qss'],
              'ilastik.ilastik_logging': ['logging_config.json'],
              '': ['*.ui']
              }

setup(name='ilastik',
      version=__version__,
      description='Interactive Image Analysis',
      url='https://github.com/Ilastik',
      packages=packages,
      package_data=package_data
     )
