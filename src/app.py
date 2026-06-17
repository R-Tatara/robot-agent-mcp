import chainlit as cl

from agent import run_agent

GREETING = "こんにちは！やってほしいことを、普段の言葉で教えてください😀\n\n例えば：\n・「左に100mm移動して」\n・「ハンドを開いて」\n\nわからないことがあれば、いつでも聞いてください👍"

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content=GREETING).send()


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history")
    answer, updated_history = await run_agent(message.content, history)
    cl.user_session.set("history", updated_history)
    await cl.Message(content=answer).send()
