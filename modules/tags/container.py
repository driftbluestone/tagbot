import discord, json, subprocess
from uuid import uuid4
from discord.ext import commands
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent.parent

async def container(ctx: commands.Context, tag: str, message: list) -> str:
    "Creates a docker container that will execute a code tag"
    container_name = uuid4().hex

    # Create the args that are passed into the container
    args = await create_args(ctx, message)
    args = json.dumps(args)
    docargs = ['docker', 'run',
               '--name', container_name,
               '--memory', '512m',
               '--memory-swap', '512m',
               '--user', '1000:1000',
               '--pids-limit', '20',
               '--cap-drop', 'ALL',
               '--network', 'none',
               '--rm', '-v', f'{DIR}/data/tags/tags:/data/:ro',
               'python', 'python3', f'/data/{tag}.py',
            ]
    
    docargs.append(args)
    try:
        result = subprocess.run(
            docargs,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5
        )
        output = result.stdout

    except subprocess.TimeoutExpired as e:
        output = e.stdout if e.stdout else ""
        # Force kill the container
        subprocess.run(
            ['docker', 'rm', '-f', container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        output = f"{output[:1900]}\n[PROCESS KILLED: exceeded 5s timeout]"
    except subprocess.CalledProcessError as e:
        output = str(e)
    return output

async def create_args(ctx: commands.context, message: list) -> dict:
    args = {}
    args["user"] = [str(ctx.author.id), ctx.author.name]
    args["server"] = [str(ctx.guild.id), ctx.guild.name]
    args["channel"] = [str(ctx.channel.id), ctx.channel.name]
    # Message history
    args["message_history"] = []
    message_history = [message async for message in ctx.message.channel.history(limit=25)]
    for i in message_history:
        i: discord.Message
        args["message_history"].append([str(i.id), i.content, str(i.author.id), i.author.name])
    # Message that was replied to, if any
    if ctx.message.reference:
        i = ctx.message.reference
        args["reference"] = [[str(i.id), i.content, str(i.author.id), i.author.name]]
    # User supplied arguments
    args["args"] = message
    return args