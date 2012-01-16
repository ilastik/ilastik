import os
import os.path
import ConfigParser

class DefaultConfigParser(ConfigParser.SafeConfigParser):
    """
    Simple extension to the default SafeConfigParser that
    accepts a default parameter in its .get method and
    returns its value when the parameter cannot be found
    in the config file instead of throwing an exception
    """
    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        if not os.path.exists(CONFIG_DIR+"config"):
            self.configfile = open(CONFIG_DIR+"config", "w+")
        else:
            self.configfile = open(CONFIG_DIR+"config", "r+")
        self.readfp(self.configfile)
        self.configfile.close()
    
    def get(self, section, option, default = None):
        """
        accepts a default parameter and returns its value
        instead of throwing an exception when the section
        or option is not found in the config file
        """
        try:
            ans = ConfigParser.SafeConfigParser.get(self, section, option)
            print ans
            return ans
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
            if default is not None:
                if e == ConfigParser.NoSectionError:
                    self.add_section(section)
                    self.set(section, option, default)
                if e == ConfigParser.NoOptionError:
                    self.set(section, option, default)
                return default
            else:
                raise e
CONFIG_DIR = os.path.expanduser("~/.lazyflow/")
if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)
CONFIG = DefaultConfigParser()
