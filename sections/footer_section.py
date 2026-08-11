import streamlit as st


def render_footer():
    st.html(
        """
        <footer class="footer">
            <strong>
                Magic Bus India Foundation
            </strong><br>
            Digital Transformation & Impact Systems<br>
            Version 2.0.0 · Developed by Narendra Shekhawat
        </footer>
        """
    )
