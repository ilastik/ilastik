from setuptools import setup

packages=['ilastik',
          'ilastik.applets',
          'ilastik.applets.base',
          'ilastik.applets.batchIo',
          'ilastik.applets.connectedComponents',
          'ilastik.applets.dataSelection',          
          'ilastik.applets.featureSelection',
          'ilastik.applets.labeling',          
          'ilastik.applets.layerViewer',
          'ilastik.applets.pixelClassification',
          'ilastik.applets.projectMetadata',
          'ilastik.applets.seededWatershed',
          'ilastik.applets.thresholdMasking',
          'ilastik.applets.vigraWatershedViewer',
          'ilastik.shell',
          'ilastik.shell.gui',
          'ilastik.shell.headless',
          'ilastik.ilastik_logging',
          'ilastik.utility',
          'ilastik.utility.gui']

package_data={'ilastik': ['ilastik-splash.png',
                          'ilastik-splash.xcf'],
          'ilastik.applets.batchIo': ['*.ui'],
          'ilastik.applets.connectedComponents': ['*.ui'],
          'ilastik.applets.dataSelection': ['*.ui'],          
          'ilastik.applets.featureSelection': ['*.ui'],
          'ilastik.applets.labeling': ['*.ui', 'icons/*.png', 'icons/*.jpg'],
          'ilastik.applets.layerViewer': ['*.ui'],
          'ilastik.applets.pixelClassification': ['*.ui'],
          'ilastik.applets.projectMetadata': ['*.ui'],
          'ilastik.applets.seededWatershed': ['*.ui'],
          'ilastik.applets.thresholdMasking': ['*.ui'],
          'ilastik.applets.vigraWatershedViewer': ['*.ui'],
          'ilastik.shell.gui': ['ui/*.ui'],
          'ilastik.ilastik_logging': ['logging_config.json']              
              }

setup(name='ilastik',
      version='0.6a',
      description='Interactive Image Analysis',
      url='https://github.com/Ilastik',
      packages=packages,
      package_data=package_data
     )
