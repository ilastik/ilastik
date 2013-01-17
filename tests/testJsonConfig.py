import os
import sys
import copy
import tempfile
import shutil
import collections
import numpy
import nose
from lazyflow.utility.jsonConfig import Namespace, JsonConfigParser, AutoEval, FormattedField

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestJsonConfigNamespace(object):
    """
    A basic test for the JsonConfigNamespace class, which always provides __dict__ as an OrderedDict.
    It should also support == and != and copy.copy().
    """
    def test(self):
        n = Namespace()
        n.a = "A"
        n.b = "B"
        n.c = "C"
        n.d = "D"
        n.e = "E"

        assert isinstance(n.__dict__, collections.OrderedDict)        
        assert n.__dict__.keys() == ["a", "b", "c", "d", "e"]
        assert n.__dict__.values() == ["A", "B", "C", "D", "E"]
        assert n.a == "A"
        assert n.b == "B"
        assert n.c == "C"
    
    def testCopy(self):
        n = Namespace()
        n.a = "A"
        n.b = "B"
        n.c = "C"

        n2 = copy.deepcopy(n)
        assert n == n2
        assert id(n) != id(n2)
        assert id(n.__dict__) != id(n2.__dict__)
        
class TestJsonConfig(object):
    
    SubConfigSchema = \
    {
        "_schema_name" : "sub-schema",
        "_schema_version" : 1.1,
        
        "sub_settingA" : str,
        "sub_settingB" : str
    }
    
    TestSchema = \
    {
        "_schema_name" : "test-schema",
        "_schema_version" : 1.1,

        "string_setting" : str,
        "int_setting" : int,
        "auto_int_setting" : AutoEval(int),
        "another_auto_int_setting" : AutoEval(int),
        "bool_setting" : bool,
        "formatted_setting" : FormattedField( requiredFields=["user_name", "user_home_town"]),
        "array_setting" : numpy.array,
        "array_from_string_setting" : AutoEval(numpy.array),
        
        "subconfig" : JsonConfigParser(SubConfigSchema)
    }
    
    @classmethod
    def setupClass(cls):
        testConfig = \
        """
        {
            "_schema_name" : "test-schema",
            "_schema_version" : 1.0,

            "string_setting" : "This is a sentence.",
            "int_setting" : 42,
            "auto_int_setting" : "7*6",
            "another_auto_int_setting" : 43,
            "bool_setting" : true,
            "formatted_setting" : "Greetings, {user_name} from {user_home_town}!",
            "array_setting" : [1,2,3,4],
            "array_from_string_setting" : "[1, 1*2, 1*3, 1*4]",
            
            "subconfig" :   {
                                "_schema_name" : "sub-schema",
                                "_schema_version" : 1.0,
                                
                                "sub_settingA" : "yes",
                                "sub_settingB" : "no"
                            }
        }
        """
        cls.tempDir = tempfile.mkdtemp()
        cls.configpath = os.path.join(cls.tempDir, "config.json")
        logger.debug("Using config file: " + cls.configpath)
        with open(cls.configpath, 'w') as f:
            f.write(testConfig)
    
    @classmethod
    def teardownClass(cls):
        # If the user is debugging, don't delete the test files.
        if logger.level > logging.DEBUG:
            shutil.rmtree(cls.tempDir)
    
    def testRead(self):
        configFields = JsonConfigParser( TestJsonConfig.TestSchema ).parseConfigFile( TestJsonConfig.configpath )

        assert configFields.string_setting == "This is a sentence."
        assert configFields.int_setting == 42
        assert configFields.auto_int_setting == 42
        assert configFields.another_auto_int_setting == 43
        assert configFields.bool_setting is True
        assert configFields.formatted_setting.format( user_name="Stuart", user_home_town="Washington, DC" ) == "Greetings, Stuart from Washington, DC!"
        
        assert isinstance(configFields.array_setting, numpy.ndarray)
        assert (configFields.array_setting == [1,2,3,4]).all()
        assert isinstance(configFields.array_from_string_setting, numpy.ndarray)
        assert (configFields.array_from_string_setting == [1,2,3,4]).all()
        
        # Check sub-config settings
        assert configFields.subconfig.sub_settingA == "yes"
        assert configFields.subconfig.sub_settingB == "no"

    def testWrite(self):
        configFields = JsonConfigParser( TestJsonConfig.TestSchema ).parseConfigFile( TestJsonConfig.configpath )
        configFields.string_setting = "This is a different sentence."
        configFields.int_setting = 100
        configFields.bool_setting = False
        
        # Write it.
        newConfigFilePath = TestJsonConfig.configpath + "_2"
        JsonConfigParser( TestJsonConfig.TestSchema ).writeConfigFile( newConfigFilePath, configFields )
        
        # Read it back.
        newConfigFields = JsonConfigParser( TestJsonConfig.TestSchema ).parseConfigFile( newConfigFilePath )
        assert newConfigFields == configFields, "Config field content was not preserved after writing/reading"
        assert configFields.__dict__.items() == configFields.__dict__.items(), "Config field ORDER was not preserved after writing/reading"

    @nose.tools.raises( JsonConfigParser.ParsingError )
    def testExceptionIfRepeatedFields(self):
        """
        This test creates a config that has an error: A field has been repeated.
        We expect to see an exception from the parser telling us that we screwed up.
        (See decorator above.)
        """

        testConfig = \
        """
        {
            "_schema_name" : "test-schema",
            "_schema_version" : 1.0,

            "string_setting" : "First instance",
            "string_setting" : "Repeated instance"
        }
        """
        tempDir = tempfile.mkdtemp()
        configpath = os.path.join(tempDir, "config.json")
        logger.debug("Using config file: " + configpath)
        with open(configpath, 'w') as f:
            f.write(testConfig)

        try:
            configFields = JsonConfigParser( TestJsonConfig.TestSchema ).parseConfigFile( configpath )
        finally:
            # Clean up temporary file
            shutil.rmtree(tempDir)

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
