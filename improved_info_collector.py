"""
Juniper Device Information Collection Script
Author: huasu@juniper.net
Version: 1.2

Purpose:
    Collects diagnostic information from Juniper devices including RSI and log files
    from both master and backup routing engines.

Prerequisites:
    - NetConf SSH must be enabled on device
    - Python 3 and junos-eznc (PyEZ) must be installed
    - User must have shell privileges
"""

from jnpr.junos import Device
from jnpr.junos.utils.fs import FS
from jnpr.junos.utils.start_shell import StartShell
from jnpr.junos.utils.scp import SCP
from jnpr.junos.exception import ConnectError
from getpass import getpass
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InfoCollector:
    def __init__(self, device_name, username, password):
        self.device_name = device_name
        self.username = username
        self.password = password
        self.device = None
        self.output_dir = '/var/tmp'
        
        # Define file names with device name
        self.rsi_file = f'rsi_{self.device_name}.txt'
        self.master_log_file = f'master_re_var_log_{self.device_name}.tgz'
        self.backup_log_file = f'backup_re_var_log_{self.device_name}.tgz'

    def connect(self):
        """Establish connection to the device"""
        try:
            self.device = Device(
                host=self.device_name,
                user=self.username,
                password=self.password,
                gather_facts=False
            )
            self.device.open()
            logger.info(f"Successfully connected to {self.device_name}")
            return True
        except ConnectError as e:
            logger.error(f"Failed to connect to device: {e}")
            return False

    def collect_rsi(self):
        """Collect RSI (Request Support Information)"""
        try:
            with StartShell(self.device) as ss:
                ss.run(f'cli -c "request support information | save /var/tmp/{self.rsi_file}"')
            logger.info("RSI collection completed")
        except Exception as e:
            logger.error(f"Failed to collect RSI: {e}")
            raise

    def collect_logs(self):
        """Collect logs from both routing engines"""
        try:
            # Collect master RE logs
            fs = FS(self.device)
            fs.tgz("/var/log/", f"/var/tmp/{self.master_log_file}")
            
            # Collect backup RE logs
            with StartShell(self.device) as ss:
                ss.run('cli -c "request routing-engine login backup"')
                ss.run("file archive compress source /var/log destination /var/tmp/backup_re_var_log")
                ss.run(f"file copy /var/tmp/backup_re_var_log.tgz /var/tmp/{self.backup_log_file}")
                ss.run(f"file copy /var/tmp/{self.backup_log_file} re0:/var/tmp")
                ss.run(f"file copy /var/tmp/{self.backup_log_file} re1:/var/tmp")
                ss.run("exit")
                
                # Verify files
                fl = ss.run(f'ls -l /var/tmp/*{self.device_name}*')
                md5 = ss.run(f'md5 /var/tmp/*{self.device_name}*')
                logger.info("File listing:\n%s", fl[1])
                logger.info("MD5 checksums:\n%s", md5[1])
            
            logger.info("Log collection completed")
        except Exception as e:
            logger.error(f"Failed to collect logs: {e}")
            raise

    def transfer_files(self):
        """Transfer collected files to local system"""
        try:
            files_to_transfer = [
                self.rsi_file,
                self.master_log_file,
                self.backup_log_file
            ]
            
            with SCP(self.device, progress=True) as scp:
                for file in files_to_transfer:
                    remote_path = f'/var/tmp/{file}'
                    local_path = os.path.join(self.output_dir, file)
                    scp.get(remote_path, local_path=local_path)
            
            logger.info("File transfer completed")
        except Exception as e:
            logger.error(f"Failed to transfer files: {e}")
            raise

    def cleanup(self):
        """Close device connection"""
        if self.device and self.device.connected:
            self.device.close()
            logger.info("Device connection closed")

def main():
    try:
        device_name = input("Device name: ")
        username = input("Username: ")
        password = getpass("Password: ")

        collector = InfoCollector(device_name, username, password)
        
        if not collector.connect():
            sys.exit(1)

        logger.info("Starting information collection (estimated time: 120 seconds)")
        collector.collect_rsi()
        collector.collect_logs()
        collector.transfer_files()

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        if collector:
            collector.cleanup()

if __name__ == "__main__":
    main()
