import threading

from controller.controller import flask_app
from frontend.tkinter_screen import run_tkinter

if __name__ == "__main__":
    # Start the Tkinter app in a separate thread
    tkinter_thread = threading.Thread(target=run_tkinter)
    tkinter_thread.start()

    # Run the Flask app in the main thread
    flask_app.run(debug=True, use_reloader=False)

    # Wait for the Tkinter thread to finish (if necessary)
    tkinter_thread.join()
