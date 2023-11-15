# LAN-Application-Multiplayer-Game
This project consists of a multiplayer game server and client, designed to allow users to play various games over a network. The server handles multiple clients, authenticating them and facilitating game sessions. The client connects to the server, allowing players to choose games and opponents.

# Server
The server is implemented in Python and handles multiple client connections using threading. It manages user authentication, game sessions, and maintains a scoreboard.

Key Features:
User Authentication: Validates player credentials.
Game Management: Supports multiple games like TicTacToe, Connect4, and Hangman.
Scoreboard: Keeps track of player scores across sessions.
Client
The client, also written in Python, connects to the server and provides an interface for the player to interact with the game server.

Key Features:
Game Selection: Players can choose from various games.
Opponent Selection: Players can select their opponents from the available online users.
Real-time Gameplay: Facilitates real-time gameplay with other players.
Games
TicTacToe
Grid-based Game: Players take turns marking a 3x3 grid.
Winning Condition: The first player to align three of their marks (vertically, horizontally, or diagonally) wins.
Connect4
Vertical Grid Game: Players drop colored discs into a 7-column, 6-row vertically suspended grid.
Winning Condition: The first player to form a horizontal, vertical, or diagonal line of four of their own discs wins.
Hangman
Word Guessing Game: One player thinks of a word, phrase, or sentence and the other tries to guess it by suggesting letters.
Usage
Start the Server: Run the server script to start listening for client connections.
Connect as a Client: Run the client script and enter your credentials to connect to the server.
Choose a Game and Opponent: Select from the available games and choose an opponent from the list of online users.
Play the Game: Follow the on-screen instructions to play the selected game.
Requirements
Python 3.x
Network connectivity between server and clients
Installation
Clone the repository or download the source code. Run the server script on the host machine and client scripts on the player's machines.

Contributing
Contributions to the project are welcome. Please ensure to follow the project's coding standards and submit a pull request for review.
