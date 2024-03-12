import random
import streamlit as st
from functools import wraps

def handle_exception(
        _func=None,
        *,  # This asterisk means that you can’t call the remaining arguments as positional arguments.
        has_funny_message_shown_on_ui=True,
        has_random_message_printed_out=False,
        funny_message="Unfortunately, our app is sleeping now 😴 Please try again when it wakes up 🫣"
    ):
    '''
        A decorator used to avoid showing technical exceptions on the UI by:
            - Showing funny messages to the users (on the UI).
            - AND printing exception message in the terminal for developers to debug.
        Parameters:
            - has_funny_message_shown_on_ui:
                Default True.
                When there is an error in your function,
                display funny_message on the UI to the user if set to True.
            - has_random_message_printed_out:
                Default False.
                When there is an error in your function,
                display random funny_message from funny_message_list below if set to True.
            - funny_message: 
                Customise this if you want to show your own error message (instead of the default one)
                Mutually exclusive with has_random_message_printed_out.
        How to use:
            - Using default args:
                @handle_exception
                def your_function_here()
            - Passing your args:
                @handle_exception(funny_message="Your customised message")
                def your_function_here()
        Reference: https://realpython.com/lessons/using-requirement-files/
    '''

    funny_message_list = [
        ":red[Unfortunately, our app is sleeping now 😴 Please try again when it wakes up 🫣]",
        ":red[Oops! Random Error - Thoughtful error 🤪]",
        ":red[Oops! ❌ Operation completed, but that doesn't mean it's error free ❌]"
    ]

    def decorator_print_funny_message(func):
        @wraps(func)
        def wrapper_print_funny_message(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                if has_random_message_printed_out:
                    random_index = random.randint(0, len(funny_message_list)-1)
                    funny_message_to_print = funny_message_list[random_index]
                else:
                    funny_message_to_print = funny_message
                result = {
                    "status": 400,
                    "value": funny_message_to_print,
                    "exception": e
                }
                if has_funny_message_shown_on_ui:
                    st.write(result.get("value"))
                print(result.get("exception"))
            return result
        return wrapper_print_funny_message

    # If you’ve called @handle_exception without arguments, 
    # then the decorated function will be passed in as _func. 
    # If you’ve called it with arguments, then _func will be None, 
    # and some of the keyword arguments may have been changed from their default values. 
    if _func is None:
        return decorator_print_funny_message
    else:
        return decorator_print_funny_message(_func)
