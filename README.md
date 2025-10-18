> [!WARNING]  
> This script DROPS your local database in order to sync it to the remote. Use carefully.

## How to use
1. Copy `exampleenv` in ./envs/<projectname>
2. Edit the new `env` with your credentials.
3. Run the project: `python3 sync.py -p <projectname>` or `uv run sync.py -p <projectname>`

### * Only tested on Linux.