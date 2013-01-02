import json
import re
import collections

class Namespace(object):
    """
    Provides the same functionality as:
    
    .. code_block:: python
    
        class Namespace(object):
            pass

    except that ``self.__dict__`` is replaced with an instance of collections.OrderedDict
        
    """
    def __init__(self):
        super(Namespace, self).__setattr__( '_items', collections.OrderedDict() )
    
    def __getattr__(self, key):
        items = super(Namespace, self).__getattribute__('_items')
        if key in items:
            return items[key]
        return super(Namespace, self).__getattribute__(key)
    
    def __setattr__(self, key, val):
        self._items[key] = val
    
    @property
    def __dict__(self):
        return self._items

    def __setstate__(self, state):
        """
        Implemented to support copy.copy()
        """
        super(Namespace, self).__setattr__( '_items', collections.OrderedDict() )
        self._items.update( state )

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        return not self.__eq__(other)

class AutoEval(object):
    """
    Callable that serves as a pseudo-type.
    Converts a value to a specific type, unless the value is a string, in which case it is evaluated first.
    """
    def __init__(self, t=None):
        """
        If a type t is provided, the value from the config will be converted using t as the constructor.
        If t is not provided, the (possibly eval'd) value will be returned 'as-is' with no conversion.
        """
        self._t = t
        if t is None:
            # If no conversion type was provided, we'll assume that the result of eval() is good enough. 
            self._t = lambda x:x
        
    def __call__(self, x):
        import numpy # We import numpy here so that eval() understands names like "numpy.uint8" and "uint8"
        from numpy import uint8, uint16, uint32, uint64, int8, int16, int32, int64, float32, float64

        if type(x) is self._t:
            return x
        if type(x) is str or type(x) is unicode and self._t is not str:
            return self._t(eval(x))
        return self._t(x)

class FormattedField(object):
    """
    Callable that serves as a pseudo-type for config values that will be used by ilastik as format strings.
    Doesn't actually transform the given value, but does check it for the required format fields.
    """
    def __init__(self, requiredFields, optionalFields=[]):
        assert isinstance(requiredFields, list)
        assert isinstance(optionalFields, list)
        
        self._requiredFields = requiredFields
        self._optionalFields = optionalFields
    
    def __call__(self, x):
        """
        Convert x to str (no unicode), and check it for the required fields.
        """
        x = str(x)
        for f in self._requiredFields:
            fieldRegex = re.compile('{[^}]*' + f +  '}')
            if fieldRegex.search(x) is None:
                raise JsonConfigSchema.ParsingError( "Format string is missing required field: {{{f}}}".format(f=f) )

        # TODO: Also validate that all format fields the user provided are known required/optional fields.
        return x    

#class AutoDirField(object):
#    def __init__(self, replaceString):
#        self._replaceString = replaceString
#    def __call__(self, x):
#        x = str(x)
#        if self._replaceString not in x:
#            return x
#        
#        # Must be /some/dir/<AUTO>, not /some/dir/<AUTO>/plus/otherstuff
#        replaceIndex = x.index(self._replaceString)
#        assert replaceIndex + len(self._replaceString) == len(x), "Auto-replaced dir name must appear at the end of the config value."
#        
#        baseDir, fileBase = os.path.split( x[0:replaceIndex] )
#        next_unused_index = 1
#        for filename in os.listdir(baseDir):
#            m = re.match("("+ fileBase + ")(\d+)", filename)
#            if m:
#                used_index = int(m.groups()[1])
#                next_unused_index = max( next_unused_index, used_index+1 )
#
#        return os.path.join( baseDir, fileBase + "{}".format(next_unused_index)  )

class JsonConfigEncoder( json.JSONEncoder ):
    def default(self, o):
        import numpy
        if isinstance(o, numpy.integer):
            return int(o)
        if isinstance(o, numpy.floating):
            return float(o)
        if isinstance(o, numpy.ndarray):
            assert len(o.shape) == 1, "No support for encoding multi-dimensional arrays in json."
            return list(o)
        if isinstance(o, Namespace):
            return(o.__dict__)
        return super( JsonConfigEncoder, self ).default(o)

class JsonConfigSchema( object ):
    """
    Simple config schema for json config files.
    Currently, only a very small set of json is supported.
    The schema fields must be a single non-nested dictionary of name : type (or pseudo-type) pairs.
    """
    class ParsingError(Exception):
        pass
    
    def __init__(self, fields, requiredSchemaName=None, requiredSchemaVersion=None):
        self._fields = dict(fields)
        assert '_schema_name' in fields.keys(), "JsonConfig Schema must have a field called '_schema_name'"
        assert '_schema_version' in fields.keys(), "JsonConfig Schema must have a field called '_schema_version'"

        # Special case for the required schema fields
        self._requiredSchemaName = self._fields['_schema_name']
        self._expectedSchemaVersion = self._fields['_schema_version']
    
        self._fields['_schema_name'] = str
        self._fields['_schema_version'] = float

    def parseConfigFile(self, configFilePath):
        with open(configFilePath) as configFile:
            try:
                jsonDict = json.load( configFile, object_pairs_hook=collections.OrderedDict )
            except:
                import sys
                sys.stderr.write( "File '{}' is not valid json.  See stdout for exception details.".format(configFilePath) )
                raise

            try:
                namespace = self._getNamespace(jsonDict)
            except JsonConfigSchema.ParsingError, e:
                raise JsonConfigSchema.ParsingError( "Error parsing config file '{f}':\n{msg}".format( f=configFilePath, msg=e.args[0] ) )

        return namespace

    def writeConfigFile(self, configFilePath, configNamespace):
        """
        Simply write the given object to a json file as a dict, 
        but check it for errors first by parsing each field with the schema.
        """
        # Check for errors by parsing the fields
        tmp = self._getNamespace(configNamespace.__dict__)

        with open(configFilePath, 'w') as configFile:
            json.dump( configNamespace.__dict__, configFile, indent=4, cls=JsonConfigEncoder )

    def __call__(self, x):
        try:
            namespace = self._getNamespace(x)
        except JsonConfigSchema.ParsingError, e:
            raise JsonConfigSchema.ParsingError( "Couldn't parse sub-config:\n{msg}".format( msg=e.args[0] ) )
        return namespace

    def _getNamespace(self, jsonDict):
        if isinstance( jsonDict, Namespace ):
            jsonDict = jsonDict.__dict__
        if not isinstance(jsonDict, collections.OrderedDict):
            raise JsonConfigSchema.ParsingError( "Expected a dict, got a {}".format( type(jsonDict) ) )
        configDict = collections.OrderedDict( (str(k) , v) for k,v in jsonDict.items() )

        namespace = Namespace()
        # Keys that the user gave us are 
        for key, value in configDict.items():
            if key in self._fields.keys():
                fieldType = self._fields[key]
                try:
                    finalValue = self._transformValue( fieldType, value )
                except JsonConfigSchema.ParsingError, e:
                    raise JsonConfigSchema.ParsingError( "Error parsing config field '{f}':\n{msg}".format( f=key, msg=e.args[0] ) )
                else:
                    setattr( namespace, key, finalValue )

        # All other config fields are None by default
        for key in self._fields.keys():
            if key not in namespace.__dict__.keys():
                setattr(namespace, key, None)

        # Check for schema errors
        if namespace._schema_name != self._requiredSchemaName:
            msg = "File schema '{}' does not match required schema '{}'".format( namespace._schema_name, self._requiredSchemaName )
            raise JsonConfigSchema.ParsingError( msg )

        # Schema versions with the same integer (not fraction) are considered backwards compatible.
        if namespace._schema_version > self._expectedSchemaVersion \
        or int(namespace._schema_version) < int(self._expectedSchemaVersion):
            msg = "File schema version '{}' is not compatible with expected schema version '{}'".format( namespace._schema_version, self._expectedSchemaVersion )
            raise JsonConfigSchema.ParsingError( msg )
                    
        return namespace
    
    def _transformValue(self, fieldType, val):
        # config file is allowed to contain null values, in which case the value is set to None
        if val is None:
            return None

        # Check special error cases
        if fieldType is bool and not isinstance(val, bool):
            raise JsonConfigSchema.ParsingError( "Expected bool, got {}".format( type(val) ) )
        
        # Other special types will error check when they construct.
        return fieldType( val )
    





