import socket
import random
import threading
import multiprocessing
from collections import defaultdict
from queue import Queue
import time
authentication_data = {
    "Adri": "1",
    "Anu": "2",
    "Moksha": "3",
    "San": "4",
    "Sam": "5"
}

available_players = {"Adri": "no", "Anu": "no",
                     "Moksha": "no", "San": "no", "Sam": "no"}
players_sockets = {}
players_ready = {}
scores = {"Adri": 0, "Anu": 0, "Moksha": 0, "San": 0, "Sam": 0}

word_dict = {
    1: "python",
    2: "socket",
    3: "hangman",
    4: "network",
    5: "server",
    6: "client",
    7: "protocol",
    8: "encode",
    9: "decode",
    10: "message"
}

hangman_drawing = [
    '''
       -----
       |   |
           |
           |
           |
           |
    ''',
    '''
       -----
       |   |
       O   |
           |
           |
           |
    ''',
    '''
       -----
       |   |
       O   |
       |   |
           |
           |
    ''',
    '''
       -----
       |   |
       O   |
      /|   |
           |
           |
    ''',
    '''
       -----
       |   |
       O   |
      /|\  |
           |
           |
    ''',
    '''
       -----
       |   |
       O   |
      /|\  |
      /    |
           |
    ''',
    '''
       -----
       |   |
       O   |
      /|\  |
      / \  |
           |
    '''
]

player_queues = defaultdict(Queue)

player_won = multiprocessing.Value('b', False)
game_in_progress = {}

players = list(authentication_data.keys())

for i in range(len(players)):
    for j in range(i + 1, len(players)):
        player1 = players[i]
        player2 = players[j]
        key1 = f"{player1}-{player2}"
        key2 = f"{player2}-{player1}"
        game_in_progress[key1] = False
        game_in_progress[key2] = False


def send_initial_messages(game_choice, client1, client2):
    if game_choice in ["TicTacToe", "Connect4"]:
        if client1:
            client1.send("Match found! You are X.".encode())
        if client2:
            client2.send("Match found! You are O.".encode())
    if game_choice == "Hangman" or game_choice == "exit" or game_choice == "ScoreBoard":
        client1.send(" ".encode())
        client2.send(" ".encode())


def send_game_over_to_other_client(client_socket, word):
    client_socket.send(
        f"Game over, Opponent Won. The word was: {word}".encode())


def get_random_word():
    return word_dict[random.randint(1, len(word_dict))]


queue_lock = threading.Lock()


def timer_thread_func(client, player_name, opponent_name):
    timer = 30
    while timer > 0:
        with queue_lock:
            if not player_queues[player_name].empty() and player_queues[player_name].get() == opponent_name:
                client.send("Match found!".encode())
                return
        timer -= 1
        time.sleep(1)
    client.send("Player not available. Please choose another player.".encode())


def handle_client_main(client):
    global game_in_progress
    while True:
        player_name = client.recv(1024).decode()
        password = client.recv(1024).decode()

        if player_name not in authentication_data or authentication_data[player_name] != password:
            client.send(
                "Authentication Failed. Invalid credentials. Please try again.".encode())
        else:
            client.send("✅ Authentication Successful".encode())
            available_players[player_name] = "yes"
            players_sockets[player_name] = client
            break
    all_players_str = ", ".join(all_player_names)
    client.send(f"👥All Players: {all_players_str}".encode())
    while True:
        name = client.recv(1024).decode()
        if name in available_players and available_players[name] == "yes" and name != player_name:
            player_queues[name].put(player_name)
            with queue_lock:
                player_queues[name].put(player_name)
            client.send("Waiting for opponent... ⏳".encode())
            timer_thread = threading.Thread(
                target=timer_thread_func, args=(client, player_name, name))
            timer_thread.start()
            timer_thread.join()
            with queue_lock:
                if not player_queues[player_name].empty() and player_queues[player_name].get() == name:
                    break
        else:
            client.send(
                "⚠️ Invalid player name or player not available. Please try again.".encode())
    players_ready[player_name] = True

    # Wait until the opponent is ready
    while not players_ready.get(name, False):
        pass

    if name in players_sockets:
        client2 = players_sockets[name]
        key1 = f"{player_name}-{name}"
        key2 = f"{name}-{player_name}"
        global game_in_progress
        if not game_in_progress.get(key1, False) and not game_in_progress.get(key2, False):
            game_in_progress[key1] = True
            game_in_progress[key2] = True
            available_players[player_name] = "no"
            available_players[name] = "no"
            # print("before calling play_game")
            play_game(client, client2, name, player_name)
            game_in_progress[key1] = False
            game_in_progress[key2] = False
            players_ready.pop(player_name, None)
            players_ready.pop(name, None)
            players_sockets.pop(player_name, None)
            players_sockets.pop(name, None)
        else:
            return


def handle_client(client_socket, other_client_socket, is_client1, word, lock, game_ongoing, game_end_event, name, player_name):
    try:
        incorrect_guesses = 0
        max_incorrect_guesses = 6
        guessed_letters = []
        while game_ongoing.value:
            with lock:
                if player_won.value:
                    client_socket.send(
                        f"Game over, Opponent Won.The word was: {word}".encode())
                    return
            try:
                guess = client_socket.recv(1024).decode().strip().lower()

                if not guess:
                    break
                with lock:
                    if game_end_event.is_set():
                        return
                    if len(guess) != 1:
                        client_socket.send(
                            "Please enter only one letter.".encode())
                        continue
                    if not guess.isalpha():
                        client_socket.send(
                            "Please enter a valid letter.".encode())
                        continue
                    if guess in guessed_letters:
                        client_socket.send(
                            "You've already guessed that letter.".encode())
                        continue

                    guessed_letters.append(guess)

                    if guess not in word:
                        incorrect_guesses += 1
                        if incorrect_guesses >= max_incorrect_guesses:
                            hangman_status = hangman_drawing[incorrect_guesses]
                            client_socket.send(
                                f"{hangman_status}\nYou Lose! The word was: {word}".encode())
                            break

                    if check_win_Hangman(word, guessed_letters):
                        winner = player_name if is_client1 else name
                        scores[winner] += 1
                        client_socket.send(
                            f"You Win! The word was: {word}".encode())
                        with player_won.get_lock():
                            player_won.value = True
                            game_ongoing.value = False
                        send_game_over_to_other_client(
                            other_client_socket, word)
                        game_end_event.set()
                        return

                    hangman_status = hangman_drawing[incorrect_guesses]
                    game_status = f"Current Hangman: {get_hangman_display(word, guessed_letters, incorrect_guesses)}"
                    client_socket.send(
                        f"{hangman_status}\n{game_status}".encode())

            except Exception as e:
                print(f"Error: {e}")
                break
    except Exception as e:
        print(f"Error: {e}")


def get_hangman_display(word, guessed_letters, incorrect_guesses):
    display = ''
    for letter in word:
        if letter in guessed_letters:
            display += letter + ' '
        else:
            display += '_ '
    display += f'   Strikes: {incorrect_guesses}/6'
    return display


def check_win_TicTacToe(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != ' ':
            return True, f"row-{i}"
    for i in range(3):
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != ' ':
            return True, f"col-{i}"
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != ' ':
        return True, "diag-0"
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != ' ':
        return True, "diag-1"
    return False, None


def check_draw(board):
    for row in board:
        for cell in row:
            if cell == ' ':
                return False
    return True


def check_win_Hangman(word, guessed_letters):
    for letter in word:
        if letter not in guessed_letters:
            return False
    return True


def check_win_Connect4(board):
    for row in range(6):
        for col in range(4):
            if board[row][col] == board[row][col + 1] == board[row][col + 2] == board[row][col + 3] and board[row][col] != ' ':
                return True, f"row-{row}-{col}"
    for col in range(7):
        for row in range(3):
            if board[row][col] == board[row + 1][col] == board[row + 2][col] == board[row + 3][col] and board[row][col] != ' ':
                return True, f"col-{col}-{row}"
    for row in range(3):
        for col in range(4):
            if board[row][col] == board[row + 1][col + 1] == board[row + 2][col + 2] == board[row + 3][col + 3] and board[row][col] != ' ':
                return True, f"diag-pos-{col}-{row}"

    for row in range(3):
        for col in range(3, 7):
            if board[row][col] == board[row + 1][col - 1] == board[row + 2][col - 2] == board[row + 3][col - 3] and board[row][col] != ' ':
                return True, f"diag-neg-{col}-{row}"

    return False, None


def play_game(client1, client2, name, player_name):

    global player_won
    # print("enter play game")
    player_won.value = False
    game_ongoing = multiprocessing.Value('b', True)
    while True:
        # print("Waiting for game choice from client1")
        game_choice1 = client1.recv(1024).decode()
        # print(f"Received game choice from client1: {game_choice1}")
        # print("Waiting for game choice from client2")
        game_choice2 = client2.recv(1024).decode()
        # print(f"Received game choice from client2: {game_choice2}")
        # print(f"Received game choice: {game_choice1}{game_choice2}")
        if game_choice1 != game_choice2 or (game_choice1 != "TicTacToe" and game_choice1 != "Connect4" and game_choice1 != "Hangman" and game_choice1 != "ScoreBoard" and game_choice1 != "Exit"):
            if client1:
                client1.send(
                    "⚠️ Game choices do not match or invalid game choice".encode())
                game_choice1 = None
            if client2:
                client2.send(
                    "⚠️ Game choices do not match or invalid game choice".encode())
                game_choice2 = None
        if game_choice1 == "Exit":
            if client1:
                client1.close()
            if client2:
                client2.close()
            return

        send_initial_messages(game_choice1, client1, client2)

        if game_choice1 == "TicTacToe":
            board = [[' ' for _ in range(3)] for _ in range(3)]
        if game_choice1 == "Connect4":
            board = [[' ' for _ in range(7)] for _ in range(6)]

        current_client = client1
        other_client = client2
        symbol = 'X'

        if game_choice1 == "TicTacToe":
            while True:
                try:
                    current_client.send("Your turn.".encode())
                    move = current_client.recv(1024).decode().split(',')

                    try:
                        x, y = int(move[0]), int(move[1])
                        if x not in [0, 1, 2] or y not in [0, 1, 2] or board[x][y] != ' ':
                            current_client.send(
                                "Invalid move. Try again.".encode())
                            continue
                    except:
                        current_client.send(
                            "Invalid input format. Use x,y format.".encode())
                        continue

                    board[x][y] = symbol

                    win, win_path = check_win_TicTacToe(board)
                    if win:
                        winner = player_name if current_client == client1 else name
                        scores[winner] += 1
                        current_client.send(f"You Win! {win_path}".encode())
                        other_client.send(f"You Lose! {win_path}".encode())
                        break

                    if check_draw(board):
                        other_client.send(
                            f"Opponent moved to {x},{y}.".encode())
                        current_client.send("It's a draw!".encode())
                        other_client.send("It's a draw!".encode())
                        break

                    other_client.send(f"Opponent moved to {x},{y}.".encode())
                    current_client, other_client = other_client, current_client
                    symbol = 'O' if symbol == 'X' else 'X'
                except ConnectionResetError:
                    other_client.send(
                        "Your opponent has left the game.".encode())
                    break

        if game_choice1 == "Connect4":
            while True:
                try:
                    current_client.send("Your turn.".encode())
                    move = current_client.recv(1024).decode().split(',')

                    try:
                        col = int(move[0])
                        if col < 0 or col >= 7 or board[0][col] != ' ':
                            current_client.send(
                                "Invalid move. Try again.".encode())
                            continue
                    except:
                        current_client.send(
                            "Invalid input format. Use column number (0-6).".encode())
                        continue

                    row = 5
                    while row >= 0 and board[row][col] != ' ':
                        row -= 1

                    board[row][col] = symbol

                    win, win_path = check_win_Connect4(board)
                    if win:
                        winner = player_name if current_client == client1 else name
                        scores[winner] += 1
                        current_client.send(f"You Win! {win_path}".encode())
                        other_client.send(f"You Lose! {win_path}".encode())
                        break

                    if check_draw(board):
                        current_client.send("It's a draw!".encode())
                        other_client.send("It's a draw!".encode())
                        break

                    other_client.send(
                        f"Opponent moved to column {col}.".encode())
                    current_client, other_client = other_client, current_client
                    symbol = 'O' if symbol == 'X' else 'X'
                except ConnectionResetError:
                    other_client.send(
                        "Your opponent has left the game.".encode())
                    break
                except Exception as e:
                    break

        if game_choice1 == "Hangman":
            game_ongoing.value = True
            player_won.value = False
            word = get_random_word()
            lock = threading.Lock()
            game_end_event = threading.Event()
            client_thread1 = threading.Thread(
                target=handle_client, args=(client1, client2, True, word, lock, game_ongoing, game_end_event, name, player_name))
            client_thread2 = threading.Thread(
                target=handle_client, args=(client2, client1, False, word, lock, game_ongoing, game_end_event, name, player_name))

            client_thread1.start()
            client_thread2.start()

            client_thread1.join()
            client_thread2.join()

        if game_choice1 == "ScoreBoard":
            client1.send(str(scores).encode())
            client2.send(str(scores).encode())


thread_event = threading.Event()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 12345))
server.listen(5)
all_player_names = list(authentication_data.keys())
print("Waiting for clients...")
while True:
    client, addr = server.accept()
    print(f"Connected with {addr}")
    client_handler = threading.Thread(
        target=handle_client_main, args=(client,))
    client_handler.start()
