import json
import re

class Namespace(object):
    pass

class AutoEval(object):
    """
    Callable that serves as a pseudo-type.
    Converts a value to a specific type, unless the value is a string, in which case it is evaluated first.
    """
    def __init__(self, t):
        self._t = t
        
    def __call__(self, x):
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


class JsonConfigSchema( object ):
    """
    Simple config schema for json config files.
    Currently, only a very small set of json is supported.
    The schema fields must be a single non-nested dictionary of name : type (or pseudo-type) pairs.
    """
    class ParsingError(Exception):
        pass
    
    def __init__(self, fields):
        self._fields = fields
    
    def parseConfigFile(self, configFilePath):
        with open(configFilePath) as configFile:
            try:
                configDict = { str(k) : v for k,v in json.load( configFile ).items() }
            except:
                import sys
                sys.stderr.write( "File '{}' is not valid json.  See stdout for exception details.".format(configFilePath) )
                raise

            try:
                return self._getNamespace(configDict)
            except JsonConfigSchema.ParsingError, e:
                raise JsonConfigSchema.ParsingError( "Error parsing config file '{f}':\n{msg}".format( f=configFilePath, msg=e.args[0] ) )

    def _getNamespace(self, configDict):
        namespace = Namespace()
        # All config fields are None by default
        for key in self._fields.keys():
            setattr(namespace, key, None)
        
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

