import streamlit as st

def injetar_pwa():
    st.markdown('''
    <link rel="manifest" href="/app/static/manifest.json">
    <meta name="theme-color" content="#0f172a">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Delta">
    <link rel="apple-touch-icon" href="/app/static/icons/icon-192.png">
    ''', unsafe_allow_html=True)
