# Community Messenger

Community Messenger is a real-time chat application built with Flask and Socket.IO. It provides a simple and effective platform for users to register, log in, and engage in conversations within a community chatroom. The application is designed to be lightweight, easy to set up, and user-friendly.

## About The Project

This project was developed to create a straightforward real-time messaging service. It leverages the power of Flask for the backend web framework, SQLAlchemy for database management, and Flask-SocketIO for handling real-time, bidirectional communication between clients and the server. The user interface is built using Bootstrap, ensuring a responsive and intuitive experience across different devices.

### Key Features

  * **User Authentication**: Secure user registration and login functionality.
  * **Real-Time Chat**: Instantaneous messaging in a community chatroom, powered by WebSockets.
  * **Simple UI**: A clean and responsive user interface designed with Bootstrap.
  * **Session Management**: Uses Flask-Login to manage user sessions, providing a persistent experience.

## Usage

Once the application is running, you can:

1.  **Register a new account**: Navigate to the registration page and create a new user profile.
2.  **Log in**: Use your credentials to log into the application.
3.  **Chat**: After logging in, you will be directed to the chat page, where you can send and receive messages in real time with other users.

## Project Structure

  * `app.py`: The main Flask application file. It contains the routes, database models, and Socket.IO event handlers.
  * `templates/`: This directory contains the HTML templates for the application, including the base layout, login, registration, and chat pages.
  * `static/`: This directory holds static files, such as the JavaScript for the chat functionality.
  * `instance/messenger.db`: The SQLite database file where user data is stored.

## Technologies Used

  * **Flask**: A lightweight WSGI web application framework in Python.
  * **Flask-SocketIO**: Integrates Socket.IO with Flask applications for real-time communication.
  * **Flask-SQLAlchemy**: A Flask extension that adds support for SQLAlchemy, an SQL toolkit and Object-Relational Mapper.
  * **Flask-Login**: Provides user session management for Flask.
  * **Socket.IO**: A library that enables real-time, bidirectional, and event-based communication.
  * **Bootstrap**: A popular CSS framework for developing responsive and mobile-first websites.

## License

This project is distributed under the MIT License. See the `LICENSE` file for more information.
