import streamlit as st

# Define a function to calculate the square of a number
def calculate_square(number):
    return number * number

# Add a text input widget for users to input a number
number_input = st.number_input("Enter a number:")

# When the user inputs a number, calculate and display its square
if number_input is not None:
    square = calculate_square(number_input)
    st.write(f"The square of {number_input} is {square}")
