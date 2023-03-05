import asyncio
import re

from EdgeGPT import Chatbot
from telebot.async_telebot import AsyncTeleBot

# --------------------------------- EDIT BELOW THIS LINE ---------------------------------

# Insert your Bot token
BOT_TOKEN = '<INSERT YOUR TELEGRAM BOT TOKEN>'
bot = AsyncTeleBot(BOT_TOKEN)

# Update your cookies.json path here
cookies_path = '<INSERT YOUR COOKIES.JSON PATH>'
gbot = Chatbot(cookiePath=cookies_path)

# Add your telegram id to the list without @ symbol
authorized_id = ['<INSERT YOUR TELEGRAM USER NAME, NOT THE DISPLAY NAME>']


# --------------------------------- DO NOT EDIT BELOW THIS LINE ---------------------------------

def update_gbot():
    global gbot
    gbot = Chatbot(cookiePath=cookies_path)


async def bing_chat(prompt, is_ref=False):
    response_dict = await gbot.ask(prompt=prompt)
    if is_ref:
        return response_dict['item']['messages'][1]["adaptiveCards"][0]["body"][0]["text"]
    return re.sub(r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['text'])


async def processing_message(message, p_msg=None, is_done=False):
    if not is_done:
        p_msg = await bot.send_message(message.chat.id, "Processing")
        await bot.send_chat_action(message.chat.id, 'typing')
        for i in range(5):
            await asyncio.sleep(1)
            await bot.edit_message_text(text=f"📡 Searching the Web{'.' * (i + 1)}", chat_id=message.chat.id,
                                        message_id=p_msg.message_id)
        for i in range(5):
            await asyncio.sleep(1)
            await bot.edit_message_text(text=f"🧠 Processing{'.' * (i + 1)}", chat_id=message.chat.id,
                                        message_id=p_msg.message_id)
        return p_msg
    else:
        await bot.delete_message(message.chat.id, p_msg.message_id)


@bot.message_handler(commands=['ask'])
async def ask(message, is_ref=False, new_topic=False):
    try:
        username = message.from_user.username
        if username not in authorized_id:
            await bot.reply_to(message, "Not authorized to use this bot")
            return
        if new_topic:
            update_gbot()
            await bot.reply_to(message, "New topic started, start a new conversation with /ask <message>")
            return
        prompt = message.text.replace("/askref", "").replace("/ask", "")
        print(f"Request received from {username} - {message.text}")
        # Call processing_message() with p_msg=None to create a new message
        pm = await processing_message(message, None)
        if not prompt:
            await bot.reply_to(message, "Empty query sent. Add your query /ask <message>")
        else:
            bot_response = await bing_chat(prompt, is_ref)
            print(f"Response received - {bot_response}")
            await bot.reply_to(message, bot_response.replace('?\n\n', ''))
        # Call processing_message() with the message object to delete the message
        await processing_message(message, pm, is_done=True)
    except Exception as e:
        print(f"Exception happened: {e}")
        # Call processing_message() with the message object to delete the message
        await processing_message(message, pm, is_done=True)
        await bot.reply_to(message, "Bing is upset! Starting a new conversation...")
        update_gbot()


@bot.message_handler(commands=['newtopic'])
async def newtopic(message):
    await ask(message, new_topic=True)


@bot.message_handler(commands=['askref'])
async def askref(message):
    await ask(message, is_ref=True)


@bot.message_handler(commands=['start'])
async def start(message):
    try:
        username = message.from_user.username
        result = f"""
        Welcome {username}!
        Start chatting with the bot by sending /ask <message>
        Chat with reference links by sending /askref <message>
        Start a new topic by sending /newtopic
        """
        await bot.send_message(message.chat.id, result)
    except Exception as e:
        print("Exception happened")
        print(e)


async def main():
    await bot.infinity_polling()


if __name__ == "__main__":
    asyncio.run(main())
