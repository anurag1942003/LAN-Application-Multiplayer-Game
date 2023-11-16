import socket
import random
import json
import ast


def display_board_TicTacToe(board):
    for row in board:
        print("|".join(row))
        print("-" * 5)


def display_board_Connect4(board):
    for row in board:
        print("|".join(row))
        print("-" * 13)


def display_strike_TicTacToe(board, path):
    if "row" in path:
        row = int(path[-1])
        board[row] = ['-' for _ in range(3)]
    elif "col" in path:
        col = int(path[-1])
        for i in range(3):
            board[i][col] = '|'
    elif "diag-0" in path:
        for i in range(3):
            board[i][i] = '\\'
    elif "diag-1" in path:
        for i in range(3):
            board[i][2-i] = '/'
    display_board_TicTacToe(board)


def display_strike_Connect4(board, path):
    if "row" in path:
        row, start_col = map(int, path.split('-')[1:])
        for col in range(start_col, start_col + 4):
            board[row][col] = '-'
    elif "col" in path:
        col, start_row = map(int, path.split('-')[1:])
        for row in range(start_row, start_row + 4):
            board[row][col] = '|'
    elif "diag-pos" in path:
        start_col, start_row = map(int, path.split('-')[2:])
        for i in range(4):
            board[start_row + i][start_col + i] = '\\'
    elif "diag-neg" in path:
        start_col, start_row = map(int, path.split('-')[2:])
        for i in range(4):
            board[start_row + i][start_col - i] = '/'


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 12345))
    while True:
        player_name = input("👤 Please enter your player name: ").capitalize()
        password = input("🔐 Please enter your password: ")
        client.send(player_name.encode())
        client.send(password.encode())
        auth_message = client.recv(1024).decode()

        if "Failed" in auth_message:
            print("🚫 Authentication Failed. Invalid credentials. Please try again.")
            print()
            continue
        print(auth_message)
        print()
        break
    all_players_message = client.recv(1024).decode()
    print(all_players_message)
    while True:
        while True:
            player_choice = input("Choose your Opponent 🗳️👉: ").capitalize()
            client.send(player_choice.encode())
            valid = client.recv(1024).decode()
            if "Please try again" in valid:
                print(valid)
                print()
                continue
            elif "Waiting for opponent..." in valid:
                print(valid)
                break
        while True:
            message = client.recv(1024).decode()
            if "Match found!" in message:
                print("\n🎊 Match Found!!! 🎊")
                break
            elif "Player not available" in message:
                print("\n ⚠️ Player not available. Please choose another player.")
                break
        if "Match found!" in message:
            break
    while True:
        print("\n")
        print("====================================")
        print("          🎮 Game Menu 🎮        ")
        print("====================================")
        print("1. TicTacToe    ❌ vs ⭕")
        print("2. Connect4     🔴 vs 🔵")
        print("3. Hangman      🕵️‍♂️ _ _ _ _ _ _ _ _")
        print("4. ScoreBoard   📊 [Player1 vs Player2]")
        print("5. Exit         🚪 [Quit the Game]    ")
        print("====================================")
        game_choice = input("Select Your Option: ")
        client.send(game_choice.encode())
        message = client.recv(1024).decode()
        if "Game choices do not match or invalid game choice" in message:
            print(message)
            continue

        if game_choice == "TicTacToe":
            board = [[' ' for _ in range(3)] for _ in range(3)]
            my_symbol = 'X' if "You are X" in message else 'O'
            opponent_symbol = 'O' if my_symbol == 'X' else 'X'

            while True:
                message = client.recv(1024).decode()
                print(message)

                if "Invalid move" in message or "Invalid input format" in message:
                    continue
                elif "Your opponent has left the game" in message:
                    break

                if "Your turn" in message:
                    display_board_TicTacToe(board)
                    while True:
                        move = input("Enter your move (x,y): ")
                        try:
                            x, y = map(int, move.split(','))
                            if x in [0, 1, 2] and y in [0, 1, 2] and board[x][y] == ' ':
                                break
                            else:
                                print("Invalid move. Try again.")
                        except ValueError:
                            print("Invalid input format. Use x,y format.")
                    board[x][y] = my_symbol
                    client.send(move.encode())

                elif "Opponent moved to" in message:
                    coords = message.split("Opponent moved to ")[
                        1].split('.')[0].split(',')
                    x, y = map(int, coords)
                    board[x][y] = opponent_symbol
                    display_board_TicTacToe(board)
                elif "You Win" in message or "You Lose" in message:
                    win_path = message.split()[-1]
                    display_strike_TicTacToe(board, win_path)
                    break

                elif "It's a draw!" in message:
                    display_board_TicTacToe(board)
                    break
                elif "Your opponent has left the game" in message:
                    break

        elif game_choice == "Connect4":
            board = [[' ' for _ in range(7)] for _ in range(6)]
            my_symbol = 'X' if "You are X" in message else 'O'
            opponent_symbol = 'O' if my_symbol == 'X' else 'X'

            while True:
                message = client.recv(1024).decode()
                print(message)

                if "Invalid move" in message or "Invalid input format" in message:
                    continue
                elif "Your opponent has left the game" in message:
                    break

                if "Your turn" in message:
                    display_board_Connect4(board)
                    while True:
                        column = input("Enter the column (0-6): ")
                        try:
                            col = int(column)
                            if col in range(7) and any(row[col] == ' ' for row in board):
                                for row in range(5, -1, -1):
                                    if board[row][col] == ' ':
                                        board[row][col] = my_symbol
                                        break
                                break
                            else:
                                print("Invalid move. Try again.")
                        except ValueError:
                            print(
                                "Invalid input format. Enter a number between 0 and 6.")
                    client.send(column.encode())

                elif "Opponent moved to" in message:
                    col = int(message.split("column ")[1].split('.')[0])
                    row = 5
                    while row >= 0 and board[row][col] != ' ':
                        row -= 1
                    board[row][col] = opponent_symbol
                    display_board_Connect4(board)
                elif "You Win" in message or "You Lose" in message:
                    win_path = message.split()[-1]
                    display_strike_Connect4(board, win_path)
                    display_board_Connect4(board)
                    break

                elif "It's a draw!" in message:
                    display_board_Connect4(board)
                    break

        elif game_choice == "Hangman":
            global game_ongoing
            game_ongoing = True
            while game_ongoing:
                try:
                    guess = input("Guess a letter: ").strip()
                    client.send(guess.encode())
                    message = client.recv(1024).decode()
                    print(message)
                    if "You Win" in message or "You Lose" in message or "Game over, Opponent Won" in message:
                        game_ongoing = False
                except ConnectionResetError:
                    print("Connection to server was lost.")
                    game_ongoing = False

                except Exception as e:
                    print(f"An error occurred: {e}")
                    game_ongoing = False
        elif game_choice == "ScoreBoard":
            scores = client.recv(1024).decode()
            scores_dict = ast.literal_eval(scores)
            print("\n")
            print("====================================")
            print("            📊 ScoreBoard 📊          ")
            print("====================================")
            print("   Player          |    Score        ")
            print("====================================")
            for key, value in scores_dict.items():
                print(f"    {key.ljust(10)}     |   {str(value).rjust(5)}")
            print("====================================")
        elif game_choice == "Exit":
            client.close()
            break


if __name__ == "__main__":
    main()
#lol
