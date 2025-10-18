import argparse
import os

from dotenv import dotenv_values
from pathvalidate import validate_filename
import subprocess
from datetime import datetime

root_status = subprocess.check_output("sudo whoami", shell=True)
if 'root' not in str(root_status):
	print("This script must be run as root.")
	exit()

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--project", type=str, required=True)

args = parser.parse_args()
project = args.project

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

print("\n======= Droping local database and creating a new one =======")
os.system(f'''sudo -u postgres psql -c "drop database {config["LOCAL_DATABASE"]};" -c "create database {config["LOCAL_DATABASE"]};" -c "alter database {config["LOCAL_DATABASE"]} owner to {config["LOCAL_USERNAME"]};"''')
print("=== Done ===")


print("\n======= Dumping remote database to ./dumps =======")
filename = f"{project}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
os.system(f"""pg_dump --no-owner --dbname=postgresql://{config["REMOTE_USERNAME"]}:{config["REMOTE_PASSWORD"]}@{config["REMOTE_HOST"]}:{config["REMOTE_PORT"]}/{config["REMOTE_DATABASE"]} --format=c  > ./dumps/{filename}""")
print(f"Saved dump to ./dumps/{filename}")
print("=== Done ===")

print(f"\n======= Restoring local database [{config['LOCAL_DATABASE']}] =======")
os.system(f'''pg_restore --no-owner --dbname 'postgresql://{config["LOCAL_USERNAME"]}:{config["LOCAL_PASSWORD"]}@localhost:{config["LOCAL_PORT"]}/{config["LOCAL_DATABASE"]}' ./dumps/{filename}''')
print("=== Done ===")