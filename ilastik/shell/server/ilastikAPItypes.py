"""Type description for various types used in communication

These types are used to automatically generate API documentation and
specification by apistar
"""
from apistar import typesystem


class LocalDataset(typesystem.Object):
    """Representation of a dataset that is local to the ilastik-server instance
    """
    properties = {
        'dataset_name': typesystem.string(
            description='name(key) of the dataset on the server'
        )
    }


class LocalProject(typesystem.Object):
    """Representation of a project that is local to the ilastik-server instance
    """
    properties = {
        'project_name': typesystem.string(
            description='name(key) of the project on the server'
        )
    }


ProjectTypes = typesystem.enum(
    description='Available workflow types',
    # TDDO: make that dynamic via a static api function?!
    enum=['PixelClassificationWorkflow', 'ObjectClassificationWorkflow'],
)


class NewLocalProject(typesystem.Object):
    properties = {
        'project_name': typesystem.string(
            description='name for the new project',
            # TODO: add length constraint,
        ),
        'project_type': ProjectTypes
    }


class Test(typesystem.Object):
    properties = {
        'var1': typesystem.string(description="string description"),
        'var2': typesystem.boolean(description="boolean value"),
        'var3': typesystem.enum(description="enum type value", enum=['a', 'b'])
    }
    description = "test type description"
