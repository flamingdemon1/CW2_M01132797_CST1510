### SmartBoyAI Database Integration

SmartBoyAI was improved so that it can answer questions using the project’s SQLite database instead of acting as a general chatbot only.

The AI does not directly access the database by itself. Instead, the Streamlit application acts as a bridge between the database and the AI. When the user asks a question, the app loads relevant dashboard tables from SQLite, creates safe summaries such as incident counts, severity counts, ticket priority counts, status counts, and dataset metadata, then passes that summary as hidden context to the AI model.

This follows the same general idea as retrieval-augmented generation, where relevant external information is retrieved and provided to an AI model as context. However, this project does not directly use the LangChain library. The retrieval/context process was implemented manually using Python, pandas, SQLite, Streamlit, and Groq.

To protect sensitive information, SmartBoyAI does not send user account data, password hashes, API keys, or full raw database tables to the AI. It only sends safe dashboard-style summaries and limited relevant dashboard rows when they are useful for answering the user’s question.

### CLI Result Saving

After previewing migrated data in the Rich CLI, a logged-in user can choose to
save the five-row result as a UTF-8 text file, a CSV file, or a record in the
project SQLite database. File exports are created in `DATA/exports/`. SQLite
exports are stored in the `saved_results` table and can be viewed later using
CLI menu option 12. Normal users can view their own saved records, while admins
can view all saved records.

The `saved_results` table stores the username, result type, title, text content,
creation time, and save source. Passwords, password hashes, and API keys are not
included in exported results.

Any additional external CSV datasets added in future coursework stages should
come from genuine sources, and their source links should be recorded clearly.

### SmartBoyAI Data Privacy Note

SmartBoyAI uses database summaries to answer project-related questions, but it does not send user login information to the AI. Passwords are stored as hashes, and account data is kept separate from the AI context. This helps the assistant provide useful dashboard insights while reducing the risk of exposing sensitive information.

### References

- Streamlit documentation was used for the chat interface and session state features.
- Streamlit secrets management documentation was used for storing the Groq API key outside the source code.
- Groq documentation was used for connecting the app to the AI model.
- LangChain retrieval-augmented generation documentation was used as a conceptual reference for retrieving project data and passing it to an AI model as context. The project does not directly use the LangChain library.
