import jujuresources

from subprocess import Popen
from path import Path
from jujubigdata import utils
from charmhelpers.core import unitdata
from shutil import copy

# Main Gobblin class for callbacks
class Gobblin(object):

    def __init__(self, dist_config):
        self.dist_config = dist_config
        self.cpu_arch = utils.cpu_arch()
        self.resources = {
            'gobblin': 'gobblin-%s' % self.cpu_arch,
        }
        self.verify_resources = utils.verify_resources(*self.resources.values())

    def is_installed(self):
        return unitdata.kv().get('gobblin.installed')

    def install(self, force=False):
        if not force and self.is_installed():
            return
        jujuresources.install(self.resources['gobblin'],
                              destination=self.dist_config.path('gobblin'),
                              skip_top_level=True)
        self.dist_config.add_users()
        self.dist_config.add_dirs()

        unitdata.kv().set('gobblin.installed', True)
        unitdata.kv().flush(True)

    def setup_gobblin(self, ip, port):
        gobblin_bin = self.dist_config.path('gobblin') / 'bin'
        with utils.environment_edit_in_place('/etc/environment') as env:
            if gobblin_bin not in env['PATH']:
                env['PATH'] = ':'.join([env['PATH'], gobblin_bin])
            env['HADOOP_BIN_DIR'] = env['HADOOP_HOME'] + '/bin'
            env['GOBBLIN_WORK_DIR'] = self.dist_config.path('outputdir')
        
        hdfs_endpoint = ''.join([ip, ':', port])

        gobblin_config_template = ''.join((self.dist_config.path('gobblin'), '/conf/gobblin-mapreduce.properties.template'))
        gobblin_config = ''.join((self.dist_config.path('gobblin'), '/conf/gobblin-mapreduce.properties'))
        copy(gobblin_config_template, gobblin_config)
        
        utils.re_edit_in_place(gobblin_config, {
                r'fs.uri=hdfs://localhost:8020': 'fs.uri=hdfs://%s' % hdfs_endpoint,
                })

    
    def run_bg(self, user, command, *args):    
        """
        Run a command as the given user in the background.
        :param str user: User to run flume agent
        :param str command: Command to run
        :param list args: Additional args to pass to the command
        """
        parts = [command] + list(args)
        quoted = ' '.join("'%s'" % p for p in parts)
        e = utils.read_etc_env()
        Popen(['su', user, '-c', quoted], env=e)



