import os
import sys
# Get the root directory of the project
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add the root directory to the Python path
sys.path.append(ROOT_DIR)
import chainlit as cl
import traceback
from pyprojroot import here
from backend.src.engine.loader import vector_query_engine, high_level_agent

@cl.on_chat_start
async def on_chat_start():
    try:
        await cl.Avatar(
            name="User",
            path=str(here("public/chitti_robot.jpg"))
        ).send()
        await cl.Message(f"Hello, welcome to the Chatbot! How can I help you?").send()
    except BaseException as e:
        print(f"Caught error on on_chat_start in app.py: {e}")
        traceback.print_exc()

@cl.on_message
async def on_message(message: cl.Message):
    try:
        msg = cl.Message(content="")
        print(message.content)
        await msg.send()
        response = vector_query_engine.query(
                message.content
            )
        
        # response = high_level_agent.chat(
        #     message.content
        # )
        await cl.Message(str(response)).send()
    except BaseException as e:
        print(f"Caught error on on_message in app.py: {e}")
        traceback.print_exc()
        await cl.Message("An error occured while processing your query. Please try again later.").send()

