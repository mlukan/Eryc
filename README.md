# Eryc
The blood donation bot, based on the Rasa Pro (CALM) framework.

This document describes the technical features of the bot. For the use case context, please read the [Introduction to Eryc](web/content/intro.md)
# Components
## Rasa training data
[Chatbot flows and patterns](./bot/data/)
[Chatbot Rasa domain file](./bot/domain/)
[Trained models](./bot/models/)
## Rasa custom actions
[Action folder](./bot/actions/)
[ORM model](./bot/actions/orm.py)
[Calendar actions](./bot/actions/calendar_actions.py)
[Calendar utils](./bot/actions/calendar_utils.py)
[Common utils](./bot/actions/common_utils.py)
[Semantic search action](./bot/actions/action_search_faiss.py)
## Database files and original FAQ data
[Calendar DB](./data/calendar.db)
[FAQ and feedback DB](./data/faq_database.db)
## Jupyter notebooks used for initial loading of FAQ DB etc.
[Notebooks](./notebooks/)
## Chat widget
[Chat widget folder](./web/)
[Frontpage with intro and chat widget](./web/index.html)

# Installation
## Requirements
[Python virtual environment](./.venv/)
[requirements.txt](./requirements.txt)
The chatbot uses a **Rasa Pro** installation based on 
**python=3.10.16
rasa-pro==3.11.2**
All packages installed in the  virtual environment are listed in the requirements file.
Access credentials to a google SMTP server are necessary for the access code/ics/QR code email delivery. Google e-mail app password must be set as environment variable 
**APP_PASSWORD**
Sender e-mail must be set as environment variable
**SENDER_EMAIL**

In case you want to use another SMTP server, the correspoding custom actions must be modified accordingly. 

The chatbot uses a custom Azure OpenAI gpt-4o model deployment for the LLM command generator.

Before running the chatbot, please train a new rasa model with a model of your choice. Change the llm model parameters in the [Rasa config file](./bot/config.yml)

The custom LLM command generator **SingleStepLLMCoGenFaF** used in the Rasa config file can be found in [single_step_llm_cogen_faf.py](./custom/single_step_llm_cogen_faf.py) and before use must be copied to the virtual environment into your Rasa Pro installation.

The **SingleStepLLMCoGenFaF** implements 2 modifications to the default SingleStepLLMCommandGenerator behavior. It allows skipping feedback choice in the feedback flow. 

It also prevents issuing StartFlow commands if slot_squat is True. This can be used for e.g. form implementations, where a user is asked to provide multiple text inputs, which could trigger unwanted digression to other flows.

## Semantic search
Semantic search does not use the Rasa Enterprise search policy, but a custom implementation which keeps the **FAISS** search index in memory of the Rasa action server. The FAQ documents of the Eryc chatbot were indexed using the **text-embedding-3-large** model from Azure OpenAI. The search function embeds the user messages using the **litellm** library. 
The environment variables
AZURE_API_BASE and AZURE_API_KEY must be set for the semantic search to work. The endpoint and API key must provide connection to a valid Azure OpenAI text-embedding-3-large model deployment. 
For other embeddings, the FAQ responses must be embedded again and saved in the DB. There are some helper functions  in the [scratch notebook](./notebooks/scratch.ipynb), which can be used for generating new embeddings, if another embedding model should be used. 
The  (example questions + response) embeddings are saved as numpy array blobs in the **embeddings** field of the faq DB table in [faq_database.db](./data/faq_database.db)
During the start of the action server, the embeddings are loaded from the **faq_database** into the **FAISS** in-memory vector store.

The **action_search_faiss** works as follows:
1. embeds the user message
2. searches the FAISS index and returns references to original responses in the **faq_database**. 
3. 3-top best matching FAQ responses are returned as search results. 
4. **gpt-4-turbo** model is used to select the most relevant document, rephrase it or generate a new curated response.

### Feedback
The user feedback is implemented using a feedback flow, filling the **slot_feedback**  with values **positive** or **negative**. If omitted, the **SingleStepLLMCoGenFaF** command generator sets the **slot_feedback** to value **pass**. This prevents the omitted feedbacks from piling up on the dialogue stack.
The **action_collect_feedback** writes  to the FAQ DB the feedback type, user message and relevant bot response which triggered the feedback in order to allow evaluation of free chatbot responses and improvement of FAQ's. 
## Language version handling
The Slovak or English language is detected by the custom action **action_initiate** at the start of the relevant flows. Conditional responses are used to selet the correct language response variation. 
