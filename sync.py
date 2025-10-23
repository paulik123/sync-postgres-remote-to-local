import argparse
import os

from dotenv import dotenv_values
from pathvalidate import validate_filename
import subprocess
from datetime import datetime
from pathlib import Path 

####### UTILS #######
def now():
	return datetime.now().isoformat(sep=" ", timespec="seconds")


root_status = subprocess.check_output("sudo whoami", shell=True)
if 'root' not in str(root_status):
	print("This script must be run as root.")
	exit()

parser = argparse.ArgumentParser()
parser.add_argument("project", nargs=1)
parser.add_argument("-ll", "--latestlocal", action='store_true', help="Skips dumping the remote database and uses the latest local version.")

args = parser.parse_args()
project = args.project[0]

try:
	validate_filename(project)
except:
	print("Invalid project name")
	exit()

if not os.path.isfile(f"./envs/{project}"):
	print("Project env does not exist in ./envs/ directory.")
	exit()



config = dotenv_values(f"./envs/{project}")

for key in [
	'REMOTE_HOST',
	'REMOTE_PORT',
	'REMOTE_DATABASE',
	'REMOTE_USERNAME',
	'REMOTE_PASSWORD',
	'LOCAL_PORT',
	'LOCAL_DATABASE',
	'LOCAL_USERNAME',
	'LOCAL_PASSWORD',
]:
	if key not in config:
		print(f"Project env does not have {key} parameter.")
		exit()

connection_status = subprocess.check_output(f"""sudo -u postgres psql -x -c \"select exists(SELECT * FROM pg_stat_activity where datname = '{config["LOCAL_DATABASE"]}')::int as connection_open;\"""", shell=True)
if 'connection_open | 1' in str(connection_status):
	print("⛔ ERROR: Local database has active connections")
	print("🦫🦫🦫 Close DBeaver/runserver boss 🦫🦫🦫")
	exit()

print(f"======= Syncing {project} =======")

print(f"[{now()}] Droping local database and creating a new one")
os.system(f'''sudo -u postgres psql -c "drop database if exists {config["LOCAL_DATABASE"]};" -c "create database {config["LOCAL_DATABASE"]};" -c "alter database {config["LOCAL_DATABASE"]} owner to {config["LOCAL_USERNAME"]};"''')
print(f"[{now()}] Done")

print()
if not args.latestlocal:
	print(f"[{now()}] Dumping remote database to ./dumps")
	filename = f"{project}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
	os.system(f"""pg_dump --no-owner --dbname=postgresql://{config["REMOTE_USERNAME"]}:{config["REMOTE_PASSWORD"]}@{config["REMOTE_HOST"]}:{config["REMOTE_PORT"]}/{config["REMOTE_DATABASE"]} --format=c  > ./dumps/{filename}""")
	print(f"[{now()}] Saved dump to ./dumps/{filename}")
	print(f"[{now()}] Done")
else:
	dumps_path = p=Path('./dumps/')
	try:
		filename = os.path.basename(max([fn for fn in p.glob('*') if project in str(fn)], key=lambda f: f.stat().st_mtime))
	except:
		print(f"⛔ ERROR: Could not find any local dump for project {project}")
		exit()
	print(f"[{now()}] Using latest local dump {filename}")

print()
print(f"[{now()}] Restoring local database [{config['LOCAL_DATABASE']}]")
os.system(f'''pg_restore --no-owner --dbname 'postgresql://{config["LOCAL_USERNAME"]}:{config["LOCAL_PASSWORD"]}@localhost:{config["LOCAL_PORT"]}/{config["LOCAL_DATABASE"]}' ./dumps/{filename}''')
print(f"[{now()}] Done")



