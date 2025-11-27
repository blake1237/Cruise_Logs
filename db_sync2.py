#!/Users/lake/.conda/envs/Cruise_Logs/bin/python
"""
SQLite Database Sync Tool
Syncs local SQLite database with remote SQLite database on spectrum.pmel.noaa.gov
User: lake (CAC/SSH key authentication)
Remote path: /home/lake/database/
"""

import sqlite3
import os
import sys
import json
import hashlib
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import getpass
import socket
import subprocess

# SSH/SCP imports
try:
    import paramiko
    from scp import SCPClient
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("Warning: paramiko not available, using system SSH/SCP commands")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SQLiteSyncSSH:
    """
    Sync SQLite databases between local machine and remote server via SSH
    """

    def __init__(self, config: Dict = None):
        """
        Initialize sync system with configuration

        Args:
            config: Dictionary with connection and sync settings
        """
        # Default configuration for user 'lake' on spectrum
        default_config = {
            'local_db': os.path.expanduser('~/Github/Cruise_Logs/Cruise_Logs.db'),
            'remote_host': 'spectrum.pmel.noaa.gov',
            'remote_user': 'lake',
            'remote_dir': '/home/spectrum/lake/database',
            'remote_db_name': 'Cruise_Logs.db',
            'backup_dir': './sync_backups',
            'metadata_file': './sync_metadata.json',
            'conflict_resolution': 'local'  # 'local', 'remote', or 'ask'
        }

        # Update with provided config
        if config:
            default_config.update(config)

        self.config = default_config
        self.local_db = self.config['local_db']
        self.remote_host = self.config['remote_host']
        self.remote_user = self.config['remote_user']
        self.remote_dir = self.config['remote_dir']
        self.remote_db = f"{self.remote_dir}/{self.config['remote_db_name']}"

        # Create backup directory
        self.backup_dir = Path(self.config.get('backup_dir', './sync_backups'))
        self.backup_dir.mkdir(exist_ok=True)

        # Track sync metadata
        self.metadata_file = Path(self.config.get('metadata_file', './sync_metadata.json'))
        self.load_metadata()

    def load_metadata(self):
        """Load sync metadata from file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                'last_sync': None,
                'sync_history': [],
                'device_id': socket.gethostname()
            }

    def save_metadata(self):
        """Save sync metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)

    def get_db_checksum(self, db_path: str) -> str:
        """Calculate SHA256 checksum of database file"""
        if not os.path.exists(db_path):
            return "FILE_NOT_FOUND"

        sha256_hash = hashlib.sha256()
        with open(db_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_db_backup(self, db_path: str, label: str = "") -> str:
        """Create a backup of the database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{Path(db_path).stem}_{label}_{timestamp}.db"
        backup_path = self.backup_dir / backup_name

        # Use SQLite's backup API for consistency
        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(str(backup_path))
        source_conn.backup(backup_conn)
        source_conn.close()
        backup_conn.close()

        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)

    def test_ssh_connection(self) -> bool:
        """Test if SSH connection works using system SSH"""
        try:
            result = subprocess.run(
                ['ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes',
                 f'{self.remote_user}@{self.remote_host}', 'echo', 'connected'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def run_remote_command(self, command: str) -> Tuple[str, str, int]:
        """Run command on remote server using system SSH"""
        try:
            result = subprocess.run(
                ['ssh', f'{self.remote_user}@{self.remote_host}', command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 1
        except Exception as e:
            return "", str(e), 1

    def connect_ssh(self) -> Optional[paramiko.SSHClient]:
        """Establish SSH connection to remote server"""
        print(f"\nConnecting to {self.remote_host} as user '{self.remote_user}'")

        # First try system SSH
        if self.test_ssh_connection():
            print("Connected via system SSH")
            return None  # Signal to use system SSH commands

        if not PARAMIKO_AVAILABLE:
            raise Exception("Cannot connect: paramiko not available and system SSH failed")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # First check if we have a valid Kerberos ticket
        try:
            import subprocess
            result = subprocess.run(['klist', '-s'], capture_output=True)
            has_kerberos = (result.returncode == 0)
            if has_kerberos:
                print("Valid Kerberos ticket detected")
            else:
                print("No valid Kerberos ticket found. You may need to run 'kinit'")
        except:
            has_kerberos = False

        # Based on your SSH config, prioritize GSSAPI/Kerberos
        auth_methods = []

        # Method 1: GSSAPI/Kerberos (primary for NOAA CAC authentication)
        if has_kerberos:
            auth_methods.append(('gssapi', None))

        # Method 2: SSH agent (fallback)
        auth_methods.append(('agent', None))

        # Method 3: SSH keys (if configured)
        ssh_key_paths = [
            os.path.expanduser('~/.ssh/id_rsa'),
            os.path.expanduser('~/.ssh/id_ed25519'),
            os.path.expanduser('~/.ssh/id_ecdsa'),
        ]

        for key_path in ssh_key_paths:
            if os.path.exists(key_path):
                auth_methods.append(('key', key_path))

        # Try each authentication method
        for method, param in auth_methods:
            try:
                if method == 'gssapi':
                    print("Trying GSSAPI/Kerberos authentication...")
                    ssh.connect(
                        hostname=self.remote_host,
                        username=self.remote_user,
                        gss_auth=True,
                        gss_kex=True,
                        timeout=30
                    )
                elif method == 'agent':
                    print("Trying SSH agent authentication...")
                    ssh.connect(
                        hostname=self.remote_host,
                        username=self.remote_user,
                        allow_agent=True,
                        look_for_keys=False,  # Don't automatically try all keys
                        timeout=30
                    )
                elif method == 'key':
                    print(f"Trying SSH key authentication with {param}...")
                    ssh.connect(
                        hostname=self.remote_host,
                        username=self.remote_user,
                        key_filename=param,
                        look_for_keys=False,
                        allow_agent=False,
                        timeout=30
                    )

                logger.info(f"Connected to {self.remote_host} using {method}")
                return ssh

            except paramiko.AuthenticationException as e:
                logger.debug(f"Authentication method {method} failed: {e}")
                continue
            except Exception as e:
                logger.debug(f"Method {method} failed: {e}")
                continue

        # If all methods fail, provide helpful error message
        error_msg = """
Authentication failed. For NOAA CAC authentication:

1. Ensure your CAC card is inserted
2. Get a Kerberos ticket by running:
   kinit

3. Or try direct SSH first to cache credentials:
   ssh {0}@{1}

4. Then retry this script.
        """.format(self.remote_user, self.remote_host)

        raise Exception(error_msg)

    def ensure_remote_dir(self, ssh: Optional[paramiko.SSHClient]):
        """Ensure remote directory exists"""
        if ssh is None:  # Using system SSH
            stdout, stderr, returncode = self.run_remote_command(f"mkdir -p {self.remote_dir}")
            if returncode != 0 and "File exists" not in stderr:
                logger.warning(f"Error creating remote directory: {stderr}")
        else:
            stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {self.remote_dir}")
            error = stderr.read().decode()
            if error and "File exists" not in error:
                logger.warning(f"Error creating remote directory: {error}")

    def get_remote_checksum(self, ssh: Optional[paramiko.SSHClient]) -> Optional[str]:
        """Get checksum of remote database"""
        try:
            if ssh is None:  # Using system SSH
                stdout, stderr, returncode = self.run_remote_command(
                    f"sha256sum {self.remote_db} 2>/dev/null || echo 'FILE_NOT_FOUND'"
                )
                result = stdout.strip()
            else:
                stdin, stdout, stderr = ssh.exec_command(
                    f"sha256sum {self.remote_db} 2>/dev/null || echo 'FILE_NOT_FOUND'"
                )
                result = stdout.read().decode().strip()

            if 'FILE_NOT_FOUND' in result:
                logger.info(f"Remote database not found: {self.remote_db}")
                return None

            checksum = result.split()[0]
            return checksum
        except Exception as e:
            logger.error(f"Failed to get remote checksum: {e}")
            return None

    def get_local_mtime(self) -> Optional[float]:
        """Get modification time of local database"""
        try:
            if os.path.exists(self.local_db):
                return os.path.getmtime(self.local_db)
            return None
        except Exception as e:
            logger.warning(f"Failed to get local mtime: {e}")
            return None

    def get_remote_mtime(self, ssh: Optional[paramiko.SSHClient]) -> Optional[float]:
        """Get modification time of remote database"""
        try:
            if ssh is None:  # Using system SSH
                # Use stat to get modification time in seconds since epoch
                stdout, stderr, returncode = self.run_remote_command(
                    f"stat -c%Y {self.remote_db} 2>/dev/null || echo 'FILE_NOT_FOUND'"
                )
                result = stdout.strip()
            else:
                stdin, stdout, stderr = ssh.exec_command(
                    f"stat -c%Y {self.remote_db} 2>/dev/null || echo 'FILE_NOT_FOUND'"
                )
                result = stdout.read().decode().strip()

            if 'FILE_NOT_FOUND' in result or not result:
                return None

            return float(result)
        except Exception as e:
            logger.warning(f"Failed to get remote mtime: {e}")
            return None

    def download_remote_db(self, ssh: Optional[paramiko.SSHClient], local_path: str):
        """Download remote database to local path"""
        try:
            if ssh is None:  # Using system SCP
                result = subprocess.run(
                    ['scp', f'{self.remote_user}@{self.remote_host}:{self.remote_db}', local_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise Exception(f"SCP failed: {result.stderr}")
            else:
                with SCPClient(ssh.get_transport()) as scp:
                    scp.get(self.remote_db, local_path)
            logger.info(f"Downloaded remote database to {local_path}")
        except Exception as e:
            logger.error(f"Failed to download remote database: {e}")
            raise

    def upload_local_db(self, ssh: Optional[paramiko.SSHClient], local_path: str):
        """Upload local database to remote server"""
        try:
            # Ensure remote directory exists
            self.ensure_remote_dir(ssh)

            # First upload to temp location
            remote_temp = f"{self.remote_db}.tmp"

            if ssh is None:  # Using system SCP
                result = subprocess.run(
                    ['scp', local_path, f'{self.remote_user}@{self.remote_host}:{remote_temp}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise Exception(f"SCP upload failed: {result.stderr}")

                # Then move atomically
                stdout, stderr, returncode = self.run_remote_command(
                    f"mv {remote_temp} {self.remote_db}"
                )
                if returncode != 0:
                    logger.error(f"Failed to move remote file: {stderr}")
                    raise Exception(stderr)
            else:
                with SCPClient(ssh.get_transport()) as scp:
                    scp.put(local_path, remote_temp)

                # Then move atomically
                stdin, stdout, stderr = ssh.exec_command(
                    f"mv {remote_temp} {self.remote_db}"
                )

                error = stderr.read().decode()
                if error:
                    logger.error(f"Failed to move remote file: {error}")
                    raise Exception(error)

            logger.info(f"Uploaded local database to {self.remote_db}")
        except Exception as e:
            logger.error(f"Failed to upload database: {e}")
            raise

    def merge_databases(self, local_db: str, remote_db: str, merged_db: str) -> Dict:
        """
        Merge two SQLite databases with conflict resolution

        Strategy:
        - For tables with timestamps: use most recent
        - For tables without: use remote (server as source of truth)
        - Track conflicts for review
        """
        stats = {
            'tables_synced': 0,
            'records_merged': 0,
            'conflicts': []
        }

        # Connect to all three databases
        local_conn = sqlite3.connect(local_db)
        remote_conn = sqlite3.connect(remote_db)
        merged_conn = sqlite3.connect(merged_db)

        try:
            # Get list of tables from both databases
            local_cursor = local_conn.cursor()
            remote_cursor = remote_conn.cursor()

            # Get tables from remote
            remote_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            remote_tables = set(row[0] for row in remote_cursor.fetchall())

            # Get tables from local
            local_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            local_tables = set(row[0] for row in local_cursor.fetchall())

            # Merge all tables (union of both)
            all_tables = remote_tables | local_tables

            for table in all_tables:
                logger.info(f"Merging table: {table}")

                # Check if table exists in both databases
                table_in_remote = table in remote_tables
                table_in_local = table in local_tables

                if table_in_remote and not table_in_local:
                    # Table only in remote - copy it
                    remote_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                    create_sql = remote_cursor.fetchone()[0]

                    merged_cursor = merged_conn.cursor()
                    merged_cursor.execute(create_sql)

                    remote_cursor.execute(f"SELECT * FROM {table}")
                    rows = remote_cursor.fetchall()

                    if rows:
                        placeholders = ','.join(['?' for _ in rows[0]])
                        merged_cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
                        stats['records_merged'] += len(rows)

                elif table_in_local and not table_in_remote:
                    # Table only in local - copy it
                    local_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                    create_sql = local_cursor.fetchone()[0]

                    merged_cursor = merged_conn.cursor()
                    merged_cursor.execute(create_sql)

                    local_cursor.execute(f"SELECT * FROM {table}")
                    rows = local_cursor.fetchall()

                    if rows:
                        placeholders = ','.join(['?' for _ in rows[0]])
                        merged_cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
                        stats['records_merged'] += len(rows)

                else:
                    # Table in both - merge records
                    # Get table schema from remote (prefer remote schema)
                    remote_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                    create_sql = remote_cursor.fetchone()[0]

                    # Create table in merged database
                    merged_cursor = merged_conn.cursor()
                    merged_cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    merged_cursor.execute(create_sql)

                    # Get column info
                    remote_cursor.execute(f"PRAGMA table_info({table})")
                    columns = remote_cursor.fetchall()
                    col_names = [col[1] for col in columns]

                    # Check for timestamp columns (for conflict resolution)
                    timestamp_cols = [col for col in col_names if
                                     'time' in col.lower() or 'date' in col.lower() or
                                     'modified' in col.lower() or 'updated' in col.lower()]

                    # Get primary key columns
                    pk_cols = [col[1] for col in columns if col[5] == 1]
                    if not pk_cols:
                        pk_cols = ['rowid']

                    # Get all remote records
                    remote_cursor.execute(f"SELECT * FROM {table}")
                    remote_records = {}
                    for row in remote_cursor.fetchall():
                        key = tuple(row[:len(pk_cols)]) if pk_cols != ['rowid'] else row[0] if row else None
                        if key is not None:
                            remote_records[key] = row

                    # Get all local records
                    local_cursor.execute(f"SELECT * FROM {table}")
                    local_records = {}
                    for row in local_cursor.fetchall():
                        key = tuple(row[:len(pk_cols)]) if pk_cols != ['rowid'] else row[0] if row else None
                        if key is not None:
                            local_records[key] = row

                    # Merge records
                    all_keys = set(remote_records.keys()) | set(local_records.keys())

                    for key in all_keys:
                        remote_row = remote_records.get(key)
                        local_row = local_records.get(key)

                        if remote_row and not local_row:
                            # Only in remote - insert
                            placeholders = ','.join(['?' for _ in col_names])
                            merged_cursor.execute(
                                f"INSERT INTO {table} VALUES ({placeholders})",
                                remote_row
                            )
                            stats['records_merged'] += 1

                        elif local_row and not remote_row:
                            # Only in local - insert
                            placeholders = ','.join(['?' for _ in col_names])
                            merged_cursor.execute(
                                f"INSERT INTO {table} VALUES ({placeholders})",
                                local_row
                            )
                            stats['records_merged'] += 1

                        else:
                            # In both - check for conflicts
                            if remote_row != local_row:
                                # Conflict - resolve based on timestamp or use remote
                                if timestamp_cols:
                                    # Compare timestamps (use first timestamp column)
                                    ts_col_idx = col_names.index(timestamp_cols[0])
                                    remote_ts = remote_row[ts_col_idx] if len(remote_row) > ts_col_idx else None
                                    local_ts = local_row[ts_col_idx] if len(local_row) > ts_col_idx else None

                                    if local_ts and remote_ts:
                                        # Use most recent
                                        use_row = local_row if local_ts > remote_ts else remote_row
                                        source = 'local' if local_ts > remote_ts else 'remote'
                                    else:
                                        # Use remote as default
                                        use_row = remote_row
                                        source = 'remote'
                                else:
                                    # No timestamp - use configured conflict resolution
                                    resolution_mode = self.config.get('conflict_resolution', 'local')
                                    if resolution_mode == 'local':
                                        use_row = local_row
                                        source = 'local'
                                    elif resolution_mode == 'remote':
                                        use_row = remote_row
                                        source = 'remote'
                                    else:  # ask
                                        print(f"\nConflict in table {table}, record {key}")
                                        print(f"Local:  {local_row}")
                                        print(f"Remote: {remote_row}")
                                        choice = input("Keep (l)ocal, (r)emote, or (s)kip? ").lower()
                                        if choice == 'l':
                                            use_row = local_row
                                            source = 'local'
                                        elif choice == 'r':
                                            use_row = remote_row
                                            source = 'remote'
                                        else:
                                            continue  # Skip this record

                                stats['conflicts'].append({
                                    'table': table,
                                    'key': key,
                                    'resolution': source
                                })
                            else:
                                # Same record - use either
                                use_row = remote_row

                            placeholders = ','.join(['?' for _ in col_names])
                            merged_cursor.execute(
                                f"INSERT INTO {table} VALUES ({placeholders})",
                                use_row
                            )
                            stats['records_merged'] += 1

                stats['tables_synced'] += 1
                merged_conn.commit()

            # Copy any indexes and triggers from remote
            remote_cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type IN ('index', 'trigger') AND sql IS NOT NULL"
            )
            for row in remote_cursor.fetchall():
                try:
                    merged_cursor.execute(row[0])
                except sqlite3.OperationalError:
                    pass  # Index/trigger might already exist

            merged_conn.commit()

        finally:
            local_conn.close()
            remote_conn.close()
            merged_conn.close()

        return stats

    def sync(self, mode: str = 'auto', conflict_resolution: str = None) -> Dict:
        """
        Perform sync operation

        Args:
            mode: 'auto' (automatic conflict resolution),
                  'download' (remote overwrites local),
                  'upload' (local overwrites remote),
                  'merge' (bidirectional with conflict resolution)
            conflict_resolution: Override default conflict resolution ('local', 'remote', 'ask')

        Returns:
            Sync statistics
        """

        # Temporarily override conflict resolution if specified
        original_resolution = self.config.get('conflict_resolution', 'local')
        if conflict_resolution:
            self.config['conflict_resolution'] = conflict_resolution
        logger.info(f"Starting sync in {mode} mode...")
        sync_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats = {'sync_id': sync_id, 'mode': mode}

        try:
            # Check if local database exists
            if not os.path.exists(self.local_db):
                print(f"Error: Local database not found: {self.local_db}")
                stats['status'] = 'failed'
                stats['error'] = 'Local database not found'
                return stats

            # Create backup of local database
            local_backup = self.create_db_backup(self.local_db, 'pre_sync')
            stats['local_backup'] = local_backup

            # Connect to server
            ssh = self.connect_ssh()

            # Get checksums
            local_checksum = self.get_db_checksum(self.local_db)
            remote_checksum = self.get_remote_checksum(ssh)

            # Get modification times for informational purposes
            local_mtime = self.get_local_mtime()
            remote_mtime = self.get_remote_mtime(ssh)

            if local_mtime and remote_mtime:
                if local_mtime > remote_mtime:
                    time_diff = self.format_time_diff(local_mtime - remote_mtime)
                    logger.info(f"Local database is newer by {time_diff}")
                    stats['time_comparison'] = f"Local is newer by {time_diff}"
                elif remote_mtime > local_mtime:
                    time_diff = self.format_time_diff(remote_mtime - local_mtime)
                    logger.info(f"Remote database is newer by {time_diff}")
                    stats['time_comparison'] = f"Remote is newer by {time_diff}"
                else:
                    stats['time_comparison'] = "Same modification time"

            if local_checksum == remote_checksum and remote_checksum is not None:
                logger.info("Databases are already in sync")
                stats['status'] = 'already_synced'
                if ssh is not None:
                    ssh.close()
                return stats

            if mode == 'download':
                if remote_checksum is None:
                    logger.warning("Remote database doesn't exist, nothing to download")
                    stats['status'] = 'no_remote'
                else:
                    # Download remote and replace local
                    temp_remote = tempfile.mktemp(suffix='.db')
                    self.download_remote_db(ssh, temp_remote)
                    shutil.move(temp_remote, self.local_db)
                    stats['status'] = 'downloaded'

            elif mode == 'upload':
                # Upload local to remote
                self.upload_local_db(ssh, self.local_db)
                stats['status'] = 'uploaded'

            elif mode in ['merge', 'auto']:
                # Bidirectional merge
                if remote_checksum is None:
                    # Remote doesn't exist - just upload local
                    logger.info("Remote database doesn't exist, uploading local database")
                    self.upload_local_db(ssh, self.local_db)
                    stats['status'] = 'uploaded_new'
                else:
                    # Both exist - perform merge
                    temp_remote = tempfile.mktemp(suffix='.db')
                    temp_merged = tempfile.mktemp(suffix='.db')

                    # Download remote
                    self.download_remote_db(ssh, temp_remote)

                    # Merge databases
                    merge_stats = self.merge_databases(
                        self.local_db,
                        temp_remote,
                        temp_merged
                    )
                    stats.update(merge_stats)

                    # Replace local with merged
                    shutil.move(temp_merged, self.local_db)

                    # Upload merged to remote
                    self.upload_local_db(ssh, self.local_db)

                    stats['status'] = 'merged'

                    # Clean up temp files
                    if os.path.exists(temp_remote):
                        os.remove(temp_remote)

            # Update metadata
            self.metadata['last_sync'] = datetime.now().isoformat()
            self.metadata['sync_history'].append({
                'sync_id': sync_id,
                'timestamp': datetime.now().isoformat(),
                'mode': mode,
                'status': stats.get('status'),
                'conflicts': len(stats.get('conflicts', []))
            })

            # Keep only last 100 sync records
            self.metadata['sync_history'] = self.metadata['sync_history'][-100:]
            self.save_metadata()

            if ssh is not None:
                ssh.close()
            logger.info(f"Sync completed successfully: {stats}")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            stats['status'] = 'failed'
            stats['error'] = str(e)

        finally:
            # Restore original conflict resolution setting
            if conflict_resolution:
                self.config['conflict_resolution'] = original_resolution

        return stats

    def show_status(self, debug=False):
        """Display sync status and history"""
        print("\n" + "="*70)
        print("SQLite Sync Status")
        print("="*70)
        print(f"Local Database:  {self.local_db}")
        print(f"Remote Server:   {self.remote_user}@{self.remote_host}")
        print(f"Remote Database: {self.remote_db}")
        print(f"Device ID:       {self.metadata.get('device_id')}")
        print(f"Last Sync:       {self.metadata.get('last_sync', 'Never')}")

        if self.metadata.get('sync_history'):
            print("\nRecent Sync History:")
            print("-"*70)
            for sync in self.metadata['sync_history'][-5:]:
                print(f"  {sync['timestamp']}: {sync['mode']} - {sync['status']}")
                if sync.get('conflicts'):
                    print(f"    Conflicts resolved: {sync['conflicts']}")

        # Check current checksums
        print("\nDatabase Status:")
        print("-"*70)
        try:
            local_mtime = None
            remote_mtime = None

            if os.path.exists(self.local_db):
                local_checksum = self.get_db_checksum(self.local_db)
                if debug:
                    print(f"Local DB Checksum:  {local_checksum}")
                else:
                    print(f"Local DB Checksum:  {local_checksum[:16]}...")

                # Get local DB size and modification time
                size_mb = os.path.getsize(self.local_db) / (1024 * 1024)
                print(f"Local DB Size:      {size_mb:.2f} MB")

                local_mtime = self.get_local_mtime()
                if local_mtime:
                    local_time_str = datetime.fromtimestamp(local_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Local DB Modified:  {local_time_str}")
            else:
                print("Local DB:           NOT FOUND")
                local_checksum = None

            print("\nChecking remote database...")
            try:
                ssh = self.connect_ssh()
            except Exception as e:
                # If paramiko fails, try system SSH
                if self.test_ssh_connection():
                    print("Using system SSH commands")
                    ssh = None
                else:
                    raise e
            remote_checksum = self.get_remote_checksum(ssh)

            if remote_checksum:
                if debug:
                    print(f"Remote DB Checksum: {remote_checksum}")
                else:
                    print(f"Remote DB Checksum: {remote_checksum[:16]}...")

                # Get remote DB size
                if ssh is None:  # Using system SSH
                    stdout, stderr, returncode = self.run_remote_command(f"stat -c%s {self.remote_db} 2>/dev/null")
                    size_str = stdout.strip()
                else:
                    stdin, stdout, stderr = ssh.exec_command(f"stat -c%s {self.remote_db} 2>/dev/null")
                    size_str = stdout.read().decode().strip()

                if size_str and size_str.isdigit():
                    size_mb = int(size_str) / (1024 * 1024)
                    print(f"Remote DB Size:     {size_mb:.2f} MB")

                # Get remote modification time
                remote_mtime = self.get_remote_mtime(ssh)
                if remote_mtime:
                    remote_time_str = datetime.fromtimestamp(remote_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Remote DB Modified: {remote_time_str}")

                # Compare databases and show recommendations
                print("\n" + "="*70)

                if local_checksum == remote_checksum:
                    print("✓ Databases are in sync")
                    if debug:
                        print(f"\n  Full checksums match: {local_checksum}")
                else:
                    print("⚠ Databases are NOT in sync")
                    if debug:
                        print(f"\n  Local:  {local_checksum}")
                        print(f"  Remote: {remote_checksum}")

                    # Show which database is newer
                    if local_mtime and remote_mtime:
                        time_diff = abs(local_mtime - remote_mtime)

                        if local_mtime > remote_mtime:
                            time_behind = self.format_time_diff(time_diff)
                            print(f"\n→ LOCAL database is NEWER by {time_behind}")
                            print("  Recommended action: 'sync upload' to update remote")
                            print("                  or: 'sync merge' to merge changes")
                        else:
                            time_behind = self.format_time_diff(time_diff)
                            print(f"\n→ REMOTE database is NEWER by {time_behind}")
                            print("  Recommended action: 'sync download' to update local")
                            print("                  or: 'sync merge' to merge changes")
                    else:
                        print("\n  Unable to determine which database is newer")
                        print("  Recommended action: 'sync merge' for safe bidirectional sync")
            else:
                print("Remote DB:          NOT FOUND")
                print("\n⚠ Remote database doesn't exist - run 'sync upload' to create it")

            if ssh is not None:
                ssh.close()

        except Exception as e:
            print(f"\nCould not check sync status: {e}")

        print("="*70 + "\n")

    def format_time_diff(self, seconds: float) -> str:
        """Format time difference in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds/60)} minutes"
        elif seconds < 86400:
            return f"{int(seconds/3600)} hours"
        else:
            return f"{int(seconds/86400)} days"

    def check_table_differences(self, table_name: str = None) -> Dict:
        """Check for differences in specific table or all tables"""
        differences = {}

        try:
            # Connect to local database
            local_conn = sqlite3.connect(self.local_db)
            local_cursor = local_conn.cursor()

            # Download remote database to temp file for comparison
            ssh = self.connect_ssh()
            temp_remote = tempfile.mktemp(suffix='.db')
            self.download_remote_db(ssh, temp_remote)

            remote_conn = sqlite3.connect(temp_remote)
            remote_cursor = remote_conn.cursor()

            # Get list of tables
            if table_name:
                tables = [table_name]
            else:
                local_cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                tables = [row[0] for row in local_cursor.fetchall()]

            for table in tables:
                # Count rows in each table
                local_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                local_count = local_cursor.fetchone()[0]

                try:
                    remote_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    remote_count = remote_cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    remote_count = 0  # Table doesn't exist in remote

                # Get checksums of table data
                local_cursor.execute(f"SELECT * FROM {table} ORDER BY rowid")
                local_data = str(local_cursor.fetchall())
                local_table_checksum = hashlib.md5(local_data.encode()).hexdigest()

                try:
                    remote_cursor.execute(f"SELECT * FROM {table} ORDER BY rowid")
                    remote_data = str(remote_cursor.fetchall())
                    remote_table_checksum = hashlib.md5(remote_data.encode()).hexdigest()
                except sqlite3.OperationalError:
                    remote_table_checksum = None

                differences[table] = {
                    'local_count': local_count,
                    'remote_count': remote_count,
                    'count_diff': local_count - remote_count,
                    'local_checksum': local_table_checksum[:8],
                    'remote_checksum': remote_table_checksum[:8] if remote_table_checksum else 'N/A',
                    'in_sync': local_table_checksum == remote_table_checksum
                }

                # If table is cruise_info, show more details
                if table == 'cruise_info' and not differences[table]['in_sync']:
                    # Get sample of different records
                    local_cursor.execute("SELECT cruise, personnel FROM cruise_info WHERE cruise LIKE '%IO6-25-FW%'")
                    local_sample = local_cursor.fetchall()

                    try:
                        remote_cursor.execute("SELECT cruise, personnel FROM cruise_info WHERE cruise LIKE '%IO6-25-FW%'")
                        remote_sample = remote_cursor.fetchall()
                    except:
                        remote_sample = []

                    differences[table]['sample_local'] = local_sample
                    differences[table]['sample_remote'] = remote_sample

            local_conn.close()
            remote_conn.close()
            if ssh is not None:
                ssh.close()

            # Clean up temp file
            if os.path.exists(temp_remote):
                os.remove(temp_remote)

        except Exception as e:
            differences['error'] = str(e)

        return differences


def main():
    """Command-line interface for sync tool"""

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = 'status'

    # Load configuration from file if exists
    config = {}
    config_file = Path('sync_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

    # Initialize sync system
    sync = SQLiteSyncSSH(config)

    if command == 'status':
        sync.show_status()

    elif command == 'debug':
        # Debug mode to check table-level differences
        print("\nDatabase Debug Information")
        print("="*70)
        print(f"Local DB Path: {sync.local_db}")
        print(f"Local DB Exists: {os.path.exists(sync.local_db)}")

        if os.path.exists(sync.local_db):
            # Show file size and modification time
            size_mb = os.path.getsize(sync.local_db) / (1024 * 1024)
            mtime = datetime.fromtimestamp(os.path.getmtime(sync.local_db))
            print(f"Local DB Size: {size_mb:.2f} MB")
            print(f"Local DB Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

            # Calculate fresh checksum
            checksum = sync.get_db_checksum(sync.local_db)
            print(f"Local DB Checksum: {checksum[:16]}...")

        print("\nChecking table-level differences...")
        print("-"*70)

        # Get specific table if provided
        table_name = sys.argv[2] if len(sys.argv) > 2 else None

        differences = sync.check_table_differences(table_name)

        if 'error' in differences:
            print(f"Error: {differences['error']}")
        else:
            print(f"{'Table':<30} {'Local':<10} {'Remote':<10} {'Diff':<10} {'Status':<10}")
            print("-"*70)

            for table, info in differences.items():
                status = "✓ SYNCED" if info['in_sync'] else "✗ DIFFERENT"
                print(f"{table:<30} {info['local_count']:<10} {info['remote_count']:<10} "
                      f"{info['count_diff']:+<10} {status:<10}")

                if not info['in_sync']:
                    print(f"  Local checksum:  {info['local_checksum']}")
                    print(f"  Remote checksum: {info['remote_checksum']}")

                    # Show sample differences for cruise_info
                    if 'sample_local' in info:
                        print(f"  Sample local records for IO6-25-FW:")
                        for record in info['sample_local']:
                            print(f"    {record}")
                        print(f"  Sample remote records for IO6-25-FW:")
                        for record in info['sample_remote']:
                            print(f"    {record}")

        print("="*70)

    elif command == 'sync':
        # Determine sync mode
        mode = sys.argv[2] if len(sys.argv) > 2 else 'merge'

        # Check for conflict resolution option
        conflict_resolution = None
        if '--local-wins' in sys.argv:
            conflict_resolution = 'local'
        elif '--remote-wins' in sys.argv:
            conflict_resolution = 'remote'
        elif '--ask' in sys.argv:
            conflict_resolution = 'ask'

        if mode not in ['merge', 'download', 'upload', 'auto']:
            print(f"Invalid sync mode: {mode}")
            print("Valid modes: merge, download, upload, auto")
            sys.exit(1)

        print(f"\nStarting {mode} sync...")
        print("="*70)

        # Show which database is newer before syncing
        print("\nChecking database modification times...")
        local_mtime = sync.get_local_mtime()

        # Quick connection to check remote
        try:
            ssh = sync.connect_ssh()
            remote_mtime = sync.get_remote_mtime(ssh)
            if ssh is not None:
                ssh.close()

            if local_mtime and remote_mtime:
                if local_mtime > remote_mtime:
                    time_diff = sync.format_time_diff(local_mtime - remote_mtime)
                    print(f"→ LOCAL database is NEWER by {time_diff}")
                elif remote_mtime > local_mtime:
                    time_diff = sync.format_time_diff(remote_mtime - local_mtime)
                    print(f"→ REMOTE database is NEWER by {time_diff}")
                else:
                    print("→ Databases have the same modification time")
        except Exception as e:
            print(f"Could not compare modification times: {e}")

        # Perform sync
        stats = sync.sync(mode, conflict_resolution=conflict_resolution)

        # Display results
        print("\nSync Results:")
        print("-"*70)
        print(f"Status: {stats.get('status', 'unknown')}")

        if stats.get('time_comparison'):
            print(f"Time comparison: {stats['time_comparison']}")

        if stats.get('tables_synced'):
            print(f"Tables synced: {stats['tables_synced']}")
            print(f"Records merged: {stats['records_merged']}")

        if stats.get('conflicts'):
            print(f"\nConflicts resolved: {len(stats['conflicts'])}")
            for conflict in stats['conflicts'][:10]:  # Show first 10
                print(f"  - {conflict['table']}: {conflict['key']} -> {conflict['resolution']}")
            if len(stats['conflicts']) > 10:
                print(f"  ... and {len(stats['conflicts']) - 10} more")

        if stats.get('error'):
            print(f"\nError: {stats['error']}")

        if stats.get('local_backup'):
            print(f"\nBackup saved: {stats['local_backup']}")

        print("="*70)

    elif command == 'backup':
        # Just create a backup
        if os.path.exists(sync.local_db):
            backup_path = sync.create_db_backup(sync.local_db, 'manual')
            print(f"Backup created: {backup_path}")
        else:
            print(f"Error: Local database not found: {sync.local_db}")

    elif command == 'config':
        # Create/update config file
        print("\nSQLite Sync Configuration")
        print("="*70)
        print("Press Enter to keep current values\n")

        current_config = sync.config

        new_config = {}
        new_config['local_db'] = input(f"Local database path [{current_config['local_db']}]: ").strip() or current_config['local_db']
        new_config['remote_host'] = input(f"Remote host [{current_config['remote_host']}]: ").strip() or current_config['remote_host']
        new_config['remote_user'] = input(f"Remote username [{current_config['remote_user']}]: ").strip() or current_config['remote_user']
        new_config['remote_dir'] = input(f"Remote directory [{current_config['remote_dir']}]: ").strip() or current_config['remote_dir']
        new_config['remote_db_name'] = input(f"Remote DB filename [{current_config['remote_db_name']}]: ").strip() or current_config['remote_db_name']

        with open('sync_config.json', 'w') as f:
            json.dump(new_config, f, indent=2)

        print("\nConfiguration saved to sync_config.json")
        print("="*70)

    else:
        print(f"\nSQLite SSH Sync Tool")
        print("="*70)
        print(f"Usage: python {os.path.basename(sys.argv[0])} [command] [options]")
        print("\nCommands:")
        print("  status        - Show sync status and check if databases match")
        print("  debug [table] - Show detailed table-level differences")
        print("  sync [mode]   - Perform sync operation")
        print("                  Modes:")
        print("                    merge    - Bidirectional merge with conflict resolution (default)")
        print("                    download - Replace local with remote database")
        print("                    upload   - Replace remote with local database")
        print("                  Options:")
        print("                    --local-wins  - Local changes win conflicts")
        print("                    --remote-wins - Remote changes win conflicts")
        print("                    --ask        - Ask for each conflict")
        print("  backup        - Create local database backup")
        print("  config        - Create/update configuration file")
        print("\nExamples:")
        print(f"  python {os.path.basename(sys.argv[0])} status")
        print(f"  python {os.path.basename(sys.argv[0])} debug")
        print(f"  python {os.path.basename(sys.argv[0])} debug cruise_info")
        print(f"  python {os.path.basename(sys.argv[0])} sync merge")
        print(f"  python {os.path.basename(sys.argv[0])} sync upload")
        print("\nDefault Settings:")
        print(f"  Local DB:  {sync.local_db}")
        print(f"  Remote:    {sync.remote_user}@{sync.remote_host}:{sync.remote_db}")
        print("="*70)


if __name__ == "__main__":
    main()
