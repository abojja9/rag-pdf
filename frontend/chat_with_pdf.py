import os
import sys
from chainlit.input_widget import Select
from llama_index.readers.web import TrafilaturaWebReader
from llama_parse import LlamaParse
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
from langchain_community.document_loaders.sitemap import SitemapLoader
# Add the root directory to the Python path
sys.path.append(ROOT_DIR)
import chainlit as cl
import traceback
from pyprojroot import here
from backend.src.utils.sitemap_urls import fetch_sitemap_urls# Get the root directory of the project
from backend.src.engine.loader import get_documents, build_index, build_query_engines

parser = LlamaParse(result_type="markdown", verbose=True, language="en")
vector_query_engine = None

@cl.on_chat_start
async def on_chat_start():
    try:
        await cl.Avatar(
            name="User",
            path=str(here("public/chitti_robot.jpg"))
        ).send()
        await cl.Message(f"Hello, welcome to the Chatbot! How can I help you?").send()
        
        settings = await cl.ChatSettings(
            [
                Select(id="app_type",
                       label="Select the Application",
                       values=[
                           "Chat with PDF", "Chat with website"]
                       ),
            ]
        ).send()
        cl.user_session.set(
            "app_type",
            settings["app_type"],
        )
    except BaseException as e:
        print(f"Caught error on on_chat_start in app.py: {e}")
        traceback.print_exc()

@cl.on_settings_update
async def setup_agent(settings):
    global vector_query_engine
    
    try:
        cl.user_session.set("app_type", settings["app_type"])
        await cl.Message(f"{settings['app_type']} is activated.").send()
        
        if cl.user_session.get("app_type") == "Chat with PDF":
            msg = cl.Message(content=f"Welcome to Chat with PDF AI Assistant...")
            await msg.send()
            files = None
            # Wait for the user to upload a PDF file
            while files is None:
                files = await cl.AskFileMessage(
                    content="Please upload a PDF file to begin!",
                    accept=["application/pdf"],
                    max_size_mb=20,
                    timeout=180,
                ).send()
            file = files[0]
            msg = cl.Message(content=f"Processing `{file.name}`...")
            await msg.send()
            documents = parser.load_data(file.path, extra_info=file.__dict__)
            vector_index, summary_index = build_index(documents=documents,
                filename=documents[0].metadata["name"])
            _, vector_query_engine, _ = build_query_engines(
                vector_index,
                summary_index,
                use_rerank=True,
                filename=documents[0].metadata["name"])
            msg = cl.Message(content=f"Let's chat with the document `{file.name}`...")
            await msg.send()
            
        elif cl.user_session.get("app_type") == "Chat with website":
            msg = cl.Message(content=f"Welcome to Chat with website AI Assistant...")
            await msg.send()
            res = await cl.AskUserMessage(content="Enter the website url you want to chat", timeout=180).send()
            if res:
                await cl.Message(
                    content=f"The website url is: {res['output']}. Please wait while we the assistant is getting the website data...",
                ).send()
                root_url = res['output']
                urls = fetch_sitemap_urls(root_url)
                urls = urls[:2] + [root_url]
                urls = list(set(urls))
                if urls and all(isinstance(url, str) for url in urls):
                    try:
                        documents = TrafilaturaWebReader().load_data(urls=urls, include_links=True)
                        # for doc in documents:
                        #     msg = cl.Message(content=doc)
                        #     await msg.send()
                        # Proceed with processing `documents`
                    except Exception as e:
                        print(f"Error loading data: {e}")
                else:
                    print("Invalid or empty URL list provided.")
                # print(urls)
                try:
                    
                    vector_index, summary_index = build_index(documents=documents,
                        filename=f"{root_url}")
                    _, vector_query_engine, _ = build_query_engines(
                        vector_index,
                        summary_index,
                        use_rerank=True,
                        filename=f"{root_url}")
                    msg = cl.Message(content=f"Let's chat with the websites: `{urls}`...")
                    await msg.send()
                except Exception as e:
                    await cl.Message(content=f"Failed to load website data due to an error: {str(e)}").send()

    except Exception as e:
        await cl.Message("An unexpected error occurred when retrieving the previous sessions. We are looking into it.").send()



@cl.on_message
async def on_message(message: cl.Message):
    try:
        msg = cl.Message(content="")
        print(message.content)
        await msg.send()
        response = vector_query_engine.query(
                message.content
            )
        await cl.Message(str(response)).send()
        
        
    except BaseException as e:
        print(f"Caught error on on_message in app.py: {e}")
        traceback.print_exc()
        await cl.Message("An error occured while processing your query. Please try again later.").send()



