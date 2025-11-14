import streamlit as st

st.set_page_config(page_title="AI Query Demo", layout="centered")

st.title("  Query Response Demo")

# Input box 
query = st.text_input("Enter your question or issue:", placeholder="e.g., My laptop won't connect to Wi-Fi")

# Button 
if st.button("Get Response"):
    if query.strip():
        
        st.success(f"Response: Based on your query, here’s a possible solution for — '{query}'")
        st.write("👉Try restarting your router and checking Wi-Fi adapter drivers.")
    else:
        st.warning("Please enter a query to get a response.")

st.caption("This is a simple Streamlit demo showing how query and response flow works.")

