import streamlit as st
import spirits

def main():

    st.title('Welcome to Blighted Island')
    st.subheader('Stats for spirit island')

    st.write(spirits.SPIRITS)

if __name__ == "__main__":
    main()
