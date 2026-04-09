import discord, json, asyncio
from uuid import uuid4
from discord.ext import commands
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent.parent

async def container(ctx: commands.Context, tag: str, message: list) -> str:
    """Creates a docker container that will execute a code tag"""
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
               args
            ]
    try:
        result = await asyncio.create_subprocess_exec(
            *docargs,
            stdout=asyncio.subprocess.PIPE  , 
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(result.communicate(), timeout=5.0)
        output = stdout.decode()
    except asyncio.TimeoutError as e:
        # Force kill the container
        kill_proc = await asyncio.create_subprocess_exec(
            'docker', 'rm', '-f', container_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await kill_proc.wait()
        output = "[PROCESS KILLED: exceeded 5s timeout]"
    except Exception as e:
        output = str(e)
    return output

async def create_args(ctx: commands.Context, message: list) -> dict:
    args = {}
    args["user"] = [ctx.author.id, ctx.author.name, ctx.author.global_name, ctx.author.nick, ctx.author.display_avatar.url]
    args["server"] = [ctx.guild.id, ctx.guild.name]
    args["channel"] = [ctx.channel.id, ctx.channel.name, ctx.channel.category.id, ctx.channel.category.name]
    # Message history
    args["message_history"] = []
    message_history = [message async for message in ctx.message.channel.history(limit=25)]
    for i in message_history:
        i: discord.Message
        args["message_history"].append([str(i.id), i.content, str(i.author.id), i.author.name, i.author.global_name, i.author.nick, ctx.author.avatar.url])
    # Message that was replied to, if any
    args["reference"] = []
    if ctx.message.reference:
        i = ctx.message.reference
        args["reference"] = [[str(i.id), i.content, str(i.author.id), i.author.name]]
    # User supplied arguments
    args["args"] = message
    return args