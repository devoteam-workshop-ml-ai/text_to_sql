from typing import Any

def dump_data(data: Any={}, filename: str="data/dumps_sql_gen.txt", mode: str="a"):
    with open(filename, mode="a") as f:
        print(f'{__name__}-{repr(data)} : {data}')
        f.write(f"{data}\n")
        f.close()