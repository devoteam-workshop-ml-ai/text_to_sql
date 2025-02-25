# text_to_sql

![image](https://github.com/user-attachments/assets/fc7eaccc-d18f-4b50-8a69-f22b6d902b00)

The ./src/app.py code is a fork of the [langchain streamlit_agent/chat_with_sql_db](https://github.com/langchain-ai/streamlit-agent/blob/main/streamlit_agent/chat_with_sql_db.py)
You can refer to this page to setup the project

## Install

1. Dependencies

    ```shell
    pip install -r requirements.txt
    ```

2. Database

    if not already done, install sqlite3

    ```shell
    sudo apt install sqlite3
    ```

    Then get Chinook.db

    ```shell
    cd ./data/database/
    curl -s https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql | sqlite3 Chinook.db
    ```

3. run

    ```shell
    streamlit run ./src/app.py
    ```
