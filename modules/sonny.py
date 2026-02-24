import random
sonny_list = ["frog", "sonny", "toad"]
reply_list = [":frog: Sonny the frog here to help!", ":frog: It seems I have been summoned!"]
async def sonny(message):
    msg = message.content
    if any(sonny in msg.lower() for sonny in sonny_list):
        await message.add_reaction("<:hyper_sonny:1471660647598002402>")
        if random.randint(1,100) == 100:
            await message.reply(random.choice(reply_list))