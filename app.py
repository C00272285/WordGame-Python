# all Imports needed for the code
from flask import Flask, render_template, request, redirect, url_for
import random
import re
import time
import mariadb

# Start of the app
app = Flask(__name__)

# List of hardcoded words between 8 - 12 letters long
WordList = [
    "adventure",
    "alligator",
    "biography",
    "breakfast",
    "celebrate",
    "dangerous",
    "discovery",
    "elephant",
    "fantastic",
    "gorgeous",
    "happiness",
    "important",
    "jubilance",
    "knowledge",
    "landscape",
    "magnolia",
    "nebulous",
    "objective",
    "philosophy",
    "quicksand",
    "radiation",
    "strawberry",
    "tournament",
    "umbrella",
    "vacuuming",
    "waterfall",
    "xylophone",
    "yearbooks",
    "zoologist",
    "quarantine",
]


# Database connection
def DatabaseConnection():
    connection = mariadb.connect(
        host="localhost",
        user="root",
        password="12July98",
        port=3308,  # My computer needs this port in order for the app to work, this may need to be changed for other
        database="WordGame",
    )
    return connection


# Function to get a random word from the hardcoded list
def GetRandomWord():
    return random.choice(WordList)


# Function to insert data into the database
def InsertData(Player, SourceWord, Matches, TimeTaken):
    connection = None
    cursor = None
    try:
        connection = DatabaseConnection()
        cursor = connection.cursor()
        # The SQL query for inserting data to the leaderboard table
        cursor.execute(
            "INSERT INTO LeaderBoard (PlayerName, WordGiven, Matches, TimeTaken) VALUES (?, ?, ?, ?)",
            (Player, SourceWord, Matches, TimeTaken),
        )
        connection.commit()
        # Error checking
    except mariadb.Error as e:
        print(f"Error inserting data: {e}")
    finally:
        # Making sure that the connection and cursor are closed
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


# Function to fetch and sort leaderboard data
def SortedLeaderBoard():
    connection = DatabaseConnection()
    cursor = connection.cursor()
    # The SQL query for getting the data in leaderboard order by Timetaken and only showing the first 10
    cursor.execute(
        "SELECT PlayerName, WordGiven, Matches, TimeTaken FROM LeaderBoard ORDER BY TimeTaken ASC LIMIT 10"
    )
    results = cursor.fetchall()
    return results


# Function to check if a word can be formed from the sourceword
def CanFormWord(word, baseword):
    basewordlist = list(
        baseword
    )  # Converting the sourceword "baseword" into a list of characters
    for char in word:
        if char in basewordlist:
            basewordlist.remove(
                char
            )  # Remove the characters form the list if it is found
        else:
            return False  # If no characters are found
    return True


# Function to validate the list of words entered by the user
def ValidateWords(WordList, baseword, minwordsrequired=7, minwords=4):
    validwords = []
    invalid = set()  # Keeps track of invaild letters
    misspelled = []
    shortwords = []
    sourcewordused = False

    for word in WordList:
        if word == baseword:
            sourcewordused = True  # If baseword is used it is flaged
        elif len(word) < minwords:
            shortwords.append(word)
        elif word not in WordList:
            misspelled.append(word)
        elif not CanFormWord(word, baseword):
            invalid.update([char for char in word if char not in baseword])
        elif word in validwords:
            pass  # Skips any dupilacated words
        else:
            validwords.append(word)  # Adds the vaild words

    feedback = []

    if invalid:
        feedback.append(f"You used these invalid letters: {', '.join(invalid)}")
    if misspelled:
        feedback.append(f"You misspelled these words: {', '.join(misspelled)}")
    if shortwords:
        feedback.append(f"These words are too short: {', '.join(shortwords)}")
    if sourcewordused:
        feedback.append(f"You cannot use the source word: {baseword}")

    if len(validwords) < minwordsrequired:
        feedback.append(
            f"You must provide at least {minwordsrequired} valid words. Currently, you have {len(validwords)} valid words."
        )

    if validwords:
        feedback.append(f"Valid words ({len(validwords)}): {', '.join(validwords)}")

    return validwords, "\n".join(feedback)  # Returns a list of vaild words


# Function to process input from the user
def ProcessInput(inputstring, baseword):
    WordList = re.split(
        r"\s+", inputstring.strip().lower()
    )  # Removes white space (" ") between words and changes the words to lowercase
    validwords, feedback = ValidateWords(WordList, baseword)  # Validate words
    return validwords, feedback


# loads the menu html
@app.route("/")
def menu():
    return render_template("Menu.html")


# loads the main game "wordgame"
@app.route("/game", methods=["GET", "POST"])
def game():
    if request.method == "POST":
        source_word = request.form["source_word"]
        user_input = request.form["user_input"]
        start_time = float(request.form["start_time"])
        validwords, results = ProcessInput(user_input, source_word)

        if len(validwords) >= 7:
            end_time = time.time()
            time_taken = round(end_time - start_time, 2)
            return render_template(
                "EnterName.html",
                source_word=source_word,
                validwords=", ".join(validwords),
                time_taken=time_taken,
            )
        else:
            return render_template(
                "Game.html", source_word=source_word, feedback=results
            )
    else:
        source_word = GetRandomWord().lower()  # Gets a random sourceword
        start_time = time.time()
        return render_template(
            "Game.html", source_word=source_word, start_time=start_time
        )


@app.route("/submit_name", methods=["POST"])
def submit_name():
    playername = request.form["playername"]
    sourceword = request.form["sourceword"]
    validwords = request.form["validwords"]
    timetaken = float(request.form["timetaken"])
    InsertData(playername, sourceword, validwords, timetaken)
    return redirect(url_for("leaderboard"))


@app.route("/leaderboard")
def leaderboard():
    leaderboard_data = SortedLeaderBoard()
    return render_template("Leaderboard.html", leaderboard=leaderboard_data)


if __name__ == "__main__":
    app.run(debug=True)
