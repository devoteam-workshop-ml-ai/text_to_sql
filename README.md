# text_to_sql

![image](https://github.com/user-attachments/assets/fc7eaccc-d18f-4b50-8a69-f22b6d902b00)

The ./app folder is based on the [langchain sql_qa tutorial](https://python.langchain.com/docs/tutorials/sql_qa/)
You can refer to this page to setup the project

## Install

1. Dependencies

    ```shell
    pip install -r requirements.txt
    ```

2. Database

    if necessary, install sqlite3

    ```shell
    sudo apt install sqlite3
    ```

    Then get Chinook.db

    ```shell
    cd ./data/database/
    curl -s https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql | sqlite3 Chinook.db
    ```

3. Setup

    * [Follow the langchain sql_qa setup tutorial](https://python.langchain.com/docs/tutorials/sql_qa/#setup)

4. run

    ```shell
    streamlit run ./src/app.py
    ```
