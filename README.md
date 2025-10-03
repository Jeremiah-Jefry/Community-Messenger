
# Community Messenger

Community Messenger is a real-time, group-based chat application built with Flask and Socket.IO. It provides a dynamic platform for users to register, create and join different chat groups, and engage in real-time conversations. Inspired by platforms like Discord and WhatsApp, it's designed to be feature-rich yet easy to set up and use.

## About The Project

This project has evolved from a simple chatroom to a multi-functional messaging service. It leverages the power of Flask for the backend, SQLAlchemy for database management, and Flask-SocketIO for handling real-time, bidirectional communication within specific group "rooms". The user interface is built using Bootstrap for a responsive, modern, and intuitive experience.

### Key Features

  * **Full User Authentication**: Secure user registration and login functionality.
  * **Group Chat System**: Users can create new chat groups, see a list of existing groups, and join them.
  * **Real-Time Messaging**: Instantaneous messaging powered by WebSockets, segregated into different group rooms.
  * **Online Presence**: See a live list of users who are currently online within each chat group.
  * **Message Timestamps**: Every message is timestamped to provide context to the conversation.
  * **Persistent Message History**: Chat history is saved to the database and loaded when a user enters a group.
  * **Admin Dashboard**: A simple dashboard to view community statistics, including the total number of registered users and their usernames.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

  * Python 3.x
  * pip (Python package installer)

### Installation

1.  **Clone the repository**

    ```sh
    git clone https://github.com/your-username/community-messenger.git
    cd community-messenger
    ```

2.  **Create and activate a virtual environment** (recommended)

     
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required packages** using the `requirements.txt` file:

    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the application**

    ```sh
    python app.py
    ```

    The application will be running at `http://127.0.0.1:5000`.

## Usage

Once the application is running, you can:

1.  **Register a new account** on the registration page.
2.  **Log in** with your new credentials.
3.  You will be directed to the **Groups page**, where you can create a new group or join an existing one.
4.  **Enter a chat room** to send and receive messages in real-time, see who else is online, and view the message history.

## Technologies Used

  * **Flask**: A lightweight WSGI web application framework in Python.
  * **Flask-SocketIO**: Integrates Socket.IO with Flask applications for real-time communication.
  * **Flask-SQLAlchemy**: A Flask extension that adds support for SQLAlchemy for database management.
  * **Flask-Login**: Provides user session management for Flask.
  * **Socket.IO**: A library that enables real-time, bidirectional, and event-based communication.
  * **Bootstrap**: A popular CSS framework for developing responsive and mobile-first websites.

## License

This project is distributed under the MIT License. See the `LICENSE` file for more information.
