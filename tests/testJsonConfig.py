import os
import sys
import tempfile
import shutil
import collections
from lazyflow.jsonConfig import Namespace, JsonConfigSchema, AutoEval, FormattedField

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestJsonConfigNamespace(object):
    
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

class TestJsonConfig(object):
    
    TestSchema = \
    {
        "_schema_name" : "test-schema",
        "_schema_version" : 1.1,

        "string_setting" : str,
        "int_setting" : int,
        "auto_int_setting" : AutoEval(int),
        "another_auto_int_setting" : AutoEval(int),
        "bool_setting" : bool,
        "formatted_setting" : FormattedField( requiredFields=["user_name", "user_home_town"])
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
            "formatted_setting" : "Greetings, {user_name} from {user_home_town}!"
        }
        """
        cls.tempDir = tempfile.mkdtemp()
        cls.configpath = os.path.join(cls.tempDir, "config.json")
        logger.debug("Using config file: " + cls.configpath)
        with open(cls.configpath, 'w') as f:
            f.write(testConfig)
    
    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls.tempDir)
    
    def testRead(self):
        configFields = JsonConfigSchema( TestJsonConfig.TestSchema ).parseConfigFile( TestJsonConfig.configpath )

        assert configFields.string_setting == "This is a sentence."
        assert configFields.int_setting == 42
        assert configFields.auto_int_setting == 42
        assert configFields.another_auto_int_setting == 43
        assert configFields.bool_setting is True
        assert configFields.formatted_setting.format( user_name="Stuart", user_home_town="Washington, DC" ) == "Greetings, Stuart from Washington, DC!"

    def testWrite(self):
        configFields = JsonConfigSchema( TestJsonConfig.TestSchema ).parseConfigFile( TestJsonConfig.configpath )
        configFields.string_setting = "This is a different sentence."
        configFields.int_setting = 100
        configFields.bool_setting = False
        
        # Write it.
        newConfigFilePath = TestJsonConfig.configpath + "_2"
        JsonConfigSchema( TestJsonConfig.TestSchema ).writeConfigFile( newConfigFilePath, configFields )
        
        # Read it back.
        newConfigFields = JsonConfigSchema( TestJsonConfig.TestSchema ).parseConfigFile( newConfigFilePath )
        assert newConfigFields.__dict__ == configFields.__dict__, "Config field content was not preserved after writing/reading"
        assert configFields.__dict__.items() == configFields.__dict__.items(), "Config field ORDER was not preserved after writing/reading"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
