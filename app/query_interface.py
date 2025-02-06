import streamlit as st

chat_input = st.chat_input("your message : ")


st.write(f"""
{chat_input}
""")
