import sqlite3 as sql
from os import path


class BookClubDB:
    # Initiailize database connection, create tables if this is the first run
    def __init__(self):
        self.filepath = 'bookClub.db'
        isInitialSetup = not path.exists(self.filepath)
        if isInitialSetup:
            with sql.connect(self.filepath) as connection:
                cursor = connection.cursor()
                cursor.execute("CREATE TABLE meetings(meetingId INTEGER NOT NULL PRIMARY KEY, active, stage, volumeId)")
                cursor.execute("CREATE TABLE submissions(meetingId INTEGER, userId INTEGER, submissionId INTEGER, volumeId)")
                cursor.execute("CREATE TABLE votes(meetingId INTEGER, userId INTEGER, firstVote INTEGER, secondVote INTEGER, thirdVote INTEGER)")
                results = cursor.execute("SELECT name FROM sqlite_master").fetchall()
                print(f"Created the following tables: {[result[0] for result in results]}")

    # SELECT (stage, volumeId)[] FROM meetings
    def getMeeting(self, meetingId):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            result = cursor.execute("SELECT stage, volumeId FROM meetings WHERE meetingId = ?", (meetingId, )).fetchone()
            return result

    # SELECT (userId, submissionId, volumeId)[] FROM submissions
    def getSubmissions(self, meetingId):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            result = cursor.execute("SELECT userId, submissionId, volumeId FROM submissions WHERE meetingId = ?", (meetingId, )).fetchall()
            return result

    # SELECT (userId, firstVote, secondVote, thirdVote)[] FROM votes
    def getVotes(self, meetingId):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            result = cursor.execute("SELECT userId, firstVote, secondVote, thirdVote FROM votes WHERE meetingId = ?", (meetingId, )).fetchall()
            return result

    # Helper function to find the currently active meeting
    def getActiveMeetingId(self) -> int:
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            result = cursor.execute("SELECT meetingId FROM meetings WHERE active = TRUE").fetchone()
            if not result:
                raise Exception('No active meeting.')
            return result[0]
    
    # Helper function to get the number of users that have made submissions in the currently active meeting
    def getSubmissionCount(self) -> int:
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            activeMeetingId = self.getActiveMeetingId()
            submissionCount = cursor.execute("SELECT COUNT(userId) FROM submissions WHERE meetingId = ?", (activeMeetingId, )).fetchone()[0]
            return submissionCount

    # Helper function to get the volumeId corresponding to a submission from the currently active meeting
    def getSubmissionVolumeId(self, submissionId: int):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            activeMeetingId = self.getActiveMeetingId()
            result = cursor.execute("SELECT volumeId FROM submissions WHERE meetingId = ? AND submissionId = ?", (activeMeetingId, submissionId)).fetchone()
            if not result:
                raise Exception(f'Missing submission {submissionId} in meeting {activeMeetingId}.')
            return result[0]

    # Set all existing meetings to inactive and create a new one
    def newMeeting(self):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE meetings SET active = FALSE")
            meetingCount = int(cursor.execute("SELECT COUNT(meetingId) FROM meetings").fetchone()[0])
            cursor.execute("INSERT INTO meetings(meetingId, active, stage) VALUES (?, 1, ?)", (meetingCount + 1, 'submit'))
            connection.commit()
            print(f"Initialized meeting {meetingCount + 1}")

    # Submit a book for the currently active meeting
    def submitBook(self, userId, volumeId):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            activeMeetingId = self.getActiveMeetingId()
            # If the user already made a submission for the currently active meeting, overwrite it
            # Otherwise, make a new submission with the submissionId being submissionCount + 1
            result = cursor.execute("SELECT submissionId FROM submissions WHERE meetingId = ? AND userId = ?", (activeMeetingId, userId)).fetchone()
            if result != None:
                cursor.execute("UPDATE submissions SET volumeId = ? WHERE meetingId = ? AND userId = ?", (volumeId, activeMeetingId, userId))
                connection.commit()
                print(f"User {userId} changed their submission to {volumeId} for meeting {activeMeetingId}")
            else:
                submissionCount = self.getSubmissionCount()
                cursor.execute("INSERT INTO submissions VALUES (?, ?, ?, ?)", (activeMeetingId, userId, submissionCount + 1, volumeId))
                connection.commit()
                print(f"User {userId} submitted a book for meeting {activeMeetingId}")
    
    # Change meeting stage to voting
    def startVoting(self):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            activeMeetingId = self.getActiveMeetingId()
            cursor.execute("UPDATE meetings SET stage = ? WHERE meetingId = ?", ('vote', activeMeetingId))
            connection.commit()
            print(f"Changed meeting stage to 'vote'")

    # Submit votes for the currently active meeting
    def vote(self, userId, firstVote, secondVote, thirdVote):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            activeMeetingId = self.getActiveMeetingId()
            cursor.execute("INSERT INTO votes VALUES (?, ?, ?, ?, ?)", (activeMeetingId, userId, firstVote, secondVote, thirdVote))
            connection.commit()
            print(f"User {userId} submitted their votes for meeting {activeMeetingId}.")

    # Change meeting stage to organized
    def endVoting(self, volumeId):
        with sql.connect(self.filepath) as connection:
            cursor = connection.cursor()
            activeMeetingId = self.getActiveMeetingId()
            cursor.execute("UPDATE meetings SET stage = ?, volumeId = ? WHERE meetingId = ?", ('organized', volumeId, activeMeetingId))
            connection.commit()
            print(f"Ended voting for meeting {activeMeetingId}, the chosen book is {volumeId}")
