---
name: Bug report
about: Create a report to help us improve

---

## Describe the bug
Please add a clear and concise description of what the bug is.

## Expected behavior
Please add a clear and concise description of what you expected to happen.

## To Reproduce
Steps to reproduce the behavior:
Within the ... workflow
1. Add some [2d/3d/4d/5d] data in the data selection applet
2. Go to ... applet, Click on '....'
3. Go to ... applet, make some annotations
4. ...

## Error message/traceback

If applicable, please add tracebacks with formatting, such as

```pytb
ERROR 2018-08-29 10:04:59,901 excepthooks 3936 140154429757184 Unhandled exception in thread: 'Worker #3'
ERROR 2018-08-29 10:04:59,901 excepthooks 3936 140154429757184 Traceback (most recent call last):
  File "/.../envs/idev/ilastik-meta/volumina/volumina/tiling.py", line 773, in _fetch_tile_layer
    img = ims_req.wait()
  File "/.../envs/idev/ilastik-meta/volumina/volumina/pixelpipeline/imagesources.py", line 387, in wait
    return self.toImage()
  File "/.../envs/idev/ilastik-meta/volumina/volumina/pixelpipeline/imagesources.py", line 425, in toImage
    raise NotImplementedError()
NotImplementedError

```


## Screenshots
If applicable, please add screenshots to help explain your problem.


## Desktop (please complete the following information):
 - ilastik version: [e.g. 1.3.2b1]
 - OS: [e.g. Ubuntu 18.04, macOS 10.12: Sierra (Fuji), Windows 10]
