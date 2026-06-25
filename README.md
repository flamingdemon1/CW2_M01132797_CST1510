### SmartBoyAI Database Integration

SmartBoyAI was improved so that it can answer questions using the project’s SQLite database instead of acting as a general chatbot only.

The AI does not directly access the database by itself. Instead, the Streamlit application acts as a bridge between the database and the AI. When the user asks a question, the app loads relevant dashboard tables from SQLite, creates safe summaries such as incident counts, severity counts, ticket priority counts, status counts, and dataset metadata, then passes that summary as hidden context to the AI model.

This follows the same general idea as retrieval-augmented generation, where relevant external information is retrieved and provided to an AI model as context. However, this project does not directly use the LangChain library. The retrieval/context process was implemented manually using Python, pandas, SQLite, Streamlit, and Groq.

To protect sensitive information, SmartBoyAI does not send user account data, password hashes, API keys, or full raw database tables to the AI. It only sends safe dashboard-style summaries and limited matching records when they are relevant to the user’s question.
