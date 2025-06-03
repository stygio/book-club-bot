import telebot
import re
import os

import customTypes as types
import constants
import library
import db
import submissionReport
import voting


if __name__ == '__main__':
    bot = telebot.TeleBot(constants.secrets['TELEGRAM_TOKEN'], parse_mode="Markdown")
    bookClubDB = db.BookClubDB()
    userSearchResults: types.UserSearchResults = {}


# Get telegram formatted user mention
def userMention(user: telebot.types.User):
    return f"[{user.first_name}](tg://user?id={str(user.id)})"

# Get dictionary of user mentions based on user IDs
def getUserMentions(chatId, userIds: list[int]):
    return { userId: (userMention(bot.get_chat_member(chatId, userId).user)) for userId in userIds }

# Get dictionary of user names based on user IDs
def getUserNames(chatId, userIds: list[int]):
    return { userId: bot.get_chat_member(chatId, userId).user.first_name for userId in userIds }

# Helper function for gating access to commands
def commandAllowed(message: telebot.types.Message, requirements: types.CommandRequirements):
    user = message.from_user
    if not user:
        bot.reply_to(message, "You are not a real user. Go away.")
        return False
    if message.chat.type != 'private' and message.chat.id != int(constants.secrets['MASTER_CHAT_ID']):
        bot.reply_to(message, f"I am configured for use in a different chat.")
        return False
    if requirements.get('chatTypes') and (not message.chat.type in requirements.get('chatTypes')):
        bot.reply_to(message, f"This command is only allowed for messages in one of these contexts: [{requirements.get('chatTypes')}]")
        return False
    if requirements.get('activeMeeting'):
        try:
            bookClubDB.getActiveMeetingId()
        except:
            bot.reply_to(message, f'There is no active meeting. My daddy needs to initiate a new meeting to begin the process.')
            return False
    if requirements.get('onlyMasterUser') and (message.from_user.id != int(constants.secrets['MASTER_USER_ID'])):
        bot.reply_to(message, f'Only daddy can tell me to do that ( ͡° ͜ʖ ͡°)')
        return False
    if requirements.get('stage'):
        activeMeetingId = bookClubDB.getActiveMeetingId()
        (stage, _) = bookClubDB.getMeeting(activeMeetingId)
        if stage != requirements.get('stage'):
            bot.reply_to(message, f"This command requires the active stage to be {requirements.get('stage')}, but it is currently {stage}.")
            return False
    return True


# Print message with instructions on how the bot operates
@bot.message_handler(commands=['instructions'])
def printInstructions(message: telebot.types.Message):
    instructionsMsg = "I am the *Book Club Bot* developed by *stygio* ([see here for more info](https://github.com/stygio/book-club-bot)).\n\n"

    instructionsMsg += "Once the admin creates a new meeting, there are two stages: submitting books and voting on books.\n\n"

    instructionsMsg += "During the *submit* stage, users submit 1 book for the active meeting.\n"
    instructionsMsg += "Find your book using the `/search <search query>` command. Once it appears in the results, choose it using the `/choose <number>` command.\n"
    instructionsMsg += "You can repeat this process and choose a different book if this phase is still ongoing.\n"
    instructionsMsg += "At the end of this phase, a submission report will be generated in PDF format with an overview of the submitted books.\n\n"

    instructionsMsg += "During the *vote* stage, users vote on 3 books submitted for the active meeting in order of preferrence.\n"
    instructionsMsg += "Vote on books in order of preferrence using the `/vote <number> <number> <number>` command.\n"
    instructionsMsg += "A winner is chosen using [Ranked-choice voting](https://ballotpedia.org/Ranked-choice_voting).\n"
    instructionsMsg += "You can repeat this process and change your vote if this phase is still ongoing.\n"
    instructionsMsg += "At the end of this phase, a table of votes will be generated and a winner will be chosen for the active meeting.\n\n"

    instructionsMsg += "The admin has some additional commands available to them. For a full list of commands with explanations, type `/commands` in a private chat with me."

    bot.reply_to(message, instructionsMsg)


# Print message with possible commands
@bot.message_handler(commands=['commands'])
def printCommands(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['private'],
    }
    if not commandAllowed(message, commandRequirements):
        return

    commandsMsg = "Here is a list of valid commands and their requirements.\n\n"
    commandsMsg += "Most commands have a list of tags (a: admin only, m: active meeting required, p: private chat, g: group chat, s: submissions stage, v: voting stage)\n\n"
    commandsMsg += "*instructions*: Prints a message with an overview of how I operate.\n\n"
    commandsMsg += "*commands* (p): Prints this message with possible commands.\n\n"
    commandsMsg += "*checkStatus* (g): Prints the current status of the meeting.\n\n"
    commandsMsg += "*newMeeting* (a/g): Initiates a new meeting.\n\n"
    commandsMsg += "*search* (m/p/s): Search the Google Books collection for a book. I will return up to 10 results. If you don't find your book, please try again with a different query. You can enter search terms directly or use the (title, author, isbn) tags to be more specific. Examples:\n`/search tolkien lord rings`\n`/search title:\"city of thieves\" author:\"david benioff\"`\n`/search isbn:9788373899292`\n\n"
    commandsMsg += "*choose* (m/p/s): Choose one of the options I returned based on your search using its number in the list of results. Example:\n`/choose 4`\n\n"
    commandsMsg += "*finishSubmissions* (a/m/g/s): Complete the submit stage and begin the vote stage.\n\n"
    commandsMsg += "*vote* (m/p/v): Vote on 3 books in order of preferrence based on their numbers in the submission report. Example:\n`/vote 5 10 2`\n\n"
    commandsMsg += "*finishVoting* (a/m/g/v): Complete the vote stage."

    bot.reply_to(message, commandsMsg)


# Check the current status of the meeting
@bot.message_handler(commands=['checkStatus'])
def checkStatus(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['group', 'supergroup'],
    }
    if not commandAllowed(message, commandRequirements):
        return

    # Check for active meeting
    try:
        activeMeetingId = bookClubDB.getActiveMeetingId()
    except:
        bot.reply_to(message, f'There is no active meeting. My daddy needs to initiate a new meeting to begin the process.')
        return

    # Check the stage of the meeting
    [stage, volumeId] = bookClubDB.getMeeting(activeMeetingId)
    match stage:
        case 'submit':
            submissionsData = bookClubDB.getSubmissions(activeMeetingId)
            # print(submissionsData)
            usersWhoSubmitted = [userId for userId, _, _ in submissionsData]
            # print(usersWhoSubmitted)
            userMentions = ', '.join(getUserMentions(message.chat.id, usersWhoSubmitted).values())
            bot.reply_to(message, f'I am currently collecting submissions for meeting {activeMeetingId}\nThe following users have submitted books: {userMentions}')
            return
        case 'vote':
            votesData = bookClubDB.getVotes(activeMeetingId)
            usersWhoVoted = [userId for userId, _, _, _ in votesData]
            userMentions = ', '.join(getUserMentions(message.chat.id, usersWhoVoted).values())
            bot.reply_to(message, f'I am currently collecting votes for meeting {activeMeetingId}.\nThe following users have voted: {userMentions}')
            return
        case 'organized':
            bookVolume = library.getBookVolume(volumeId)
            bot.reply_to(message, f'Meeting {activeMeetingId} has been organized.\n{library.formatBookVolume(bookVolume)} was chosen.')
            return
        case _:
            raise Exception(f'Invalid stage: {stage}')


# Initiate a new meeting
@bot.message_handler(commands=['newMeeting'])
def newMeeting(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['group', 'supergroup'],
        'onlyMasterUser': True,
    }
    if not commandAllowed(message, commandRequirements):
        return

    bookClubDB.newMeeting()
    activeMeetingId = bookClubDB.getActiveMeetingId()
    
    bot.reply_to(message, f'I have initiated meeting number {activeMeetingId} for the book club.')

# Begin the process of submitting a book
@bot.message_handler(commands=['search'])
def search(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['private'],
        'activeMeeting': True,
        'stage': 'submit',
    }
    if not commandAllowed(message, commandRequirements):
        return

    numFound, searchResults = library.findBookVolumes(message.text)
    if numFound == 0:
        bot.reply_to(message, "No results found, please try again.")
        return

    userSearchResults[message.from_user.id] = searchResults
    replyString = f'I found {numFound} results for your search'
    replyString += f', these are the top {constants.MAX_SEARCH_RESULTS}:\n' if numFound > constants.MAX_SEARCH_RESULTS else ':\n'
    # This loop shortens the results if needed (rare) so as to respect Telegram's 4096 character limit per message
    while True:
        tmpReplyString = replyString + library.formatBookVolumeList(searchResults)
        if len(tmpReplyString) < 4096:
            replyString = tmpReplyString
            break
        searchResults = searchResults[:-1]

    bot.reply_to(message, replyString)


# Submit a book from the user's previous search result
@bot.message_handler(commands=['choose'])
def chooseSubmission(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['private'],
        'activeMeeting': True,
        'stage': 'submit',
    }
    if not commandAllowed(message, commandRequirements):
        return
    userId = message.from_user.id

    chooseMatch = re.match(constants.regex['CHOOSE'], message.text)
    if not chooseMatch:
        bot.reply_to(message, 'Your message does not conform to the expected format of `/choose <number>`.')
        return
    searchResults = userSearchResults.get(userId)
    if not searchResults:
        bot.reply_to(message, 'You have no search results to choose from. Have you used the `/search <search expression>` command yet?')
        return
    # User input is indexed 1-10, array is indexed 0-9
    choiceStr = chooseMatch.group(1)
    choiceIdx = int(choiceStr) - 1
    if not (choiceIdx >= 0 and choiceIdx < len(searchResults)):
        bot.reply_to(message, f'Your choice ({choiceStr}) is not valid, expected something in the range of 1 - {len(searchResults)}.')
        return

    bookClubDB.submitBook(userId, searchResults[choiceIdx]['id'])
    replyString = f"I saved your choice of {library.formatBookVolume(searchResults[choiceIdx])}."

    bot.reply_to(message, replyString)


# Finalize the submit stage, generate a submission report and begin the vote stage
@bot.message_handler(commands=['finishSubmissions'])
def finishSubmissions(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['group', 'supergroup'],
        'activeMeeting': True,
        'onlyMasterUser': True,
        'stage': 'submit',
    }
    if not commandAllowed(message, commandRequirements):
        return

    # Generate report
    activeMeetingId = bookClubDB.getActiveMeetingId()
    submissions = { submissionId: library.getBookVolume(volumeId) for (_, submissionId, volumeId) in bookClubDB.getSubmissions(activeMeetingId) }
    if len(submissions.keys()) == 0:
        bot.reply_to(message, f'No submissions found, please submit some books for the active meeting.')
        return
    submissionReportFilePath = submissionReport.generate(activeMeetingId, submissions)
    with open(submissionReportFilePath, 'rb') as doc:
        bot.send_document(message.chat.id, doc, None, f"Meeting {activeMeetingId} of the Wild Frog Book Club: Submission Overview")
    os.remove(submissionReportFilePath)
    # Begin vote stage
    bookClubDB.startVoting()

    bot.reply_to(message, f'The voting stage has begun. Please have a look at the submission overview I generated and vote based on their IDs.')


# Vote on three books (descending order of priority) from the submissions in the active meeting
@bot.message_handler(commands=['vote'])
def vote(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['private'],
        'activeMeeting': True,
        'stage': 'vote',
    }
    if not commandAllowed(message, commandRequirements):
        return
    userId = message.from_user.id

    voteMatch = re.match(constants.regex['VOTE'], message.text)
    if not voteMatch:
        bot.reply_to(message, 'Your message does not conform to the expected format of `/vote <first choice number> <second choice number> <third choice number>`.')
        return
    choices: list[str] = re.match(constants.regex['VOTE'], message.text).groups()
    submissionCount = bookClubDB.getSubmissionCount()
    for choice in choices:
        choice = int(choice)
        if not (choice > 0 and choice <= submissionCount):
            bot.reply_to(message, f'Your choice ({choice}) is not valid, expected something in the range of 1 - {submissionCount}.')
            return
    if choices[0] == choices[1] or choices[1] == choices[2] or choices[0] == choices[2]:
        bot.reply_to(message, f'You need to choose three different books')
        return

    bookClubDB.vote(userId, choices[0], choices[1], choices[2])
    chosenBooks = []
    for choice in choices:
        choice = int(choice)
        volumeId = bookClubDB.getSubmissionVolumeId(choice)
        chosenBooks.append(library.getBookVolume(volumeId))

    bot.reply_to(message, f'Successfully saved your votes:\n{library.formatBookVolumeList(chosenBooks)}')


# Finalize the vote stage and choose the winning submission
@bot.message_handler(commands=['finishVoting'])
def finishVoting(message: telebot.types.Message):
    commandRequirements: types.CommandRequirements = {
        'chatTypes': ['group', 'supergroup'],
        'activeMeeting': True,
        'onlyMasterUser': True,
        'stage': 'vote',
    }
    if not commandAllowed(message, commandRequirements):
        return
    
    # Gather data from BookClubDB
    activeMeetingId = bookClubDB.getActiveMeetingId()
    # Votes
    userVotes = { int(userId): [int(firstVote), int(secondVote), int(thirdVote)] for userId, firstVote, secondVote, thirdVote in bookClubDB.getVotes(activeMeetingId) }
    if len(userVotes.keys()) == 0:
        bot.reply_to(message, f'No votes found, cannot perform voting process.')
        return
    # Submissions
    submissions = { int(submissionId): library.getBookVolume(volumeId) for (_, submissionId, volumeId) in bookClubDB.getSubmissions(activeMeetingId) }
    # Perform vote
    userNames = getUserNames(message.chat.id, userVotes.keys())
    winner = voting.performVote(userVotes, submissions)
    voteTable = voting.drawVoteTable(userVotes, submissions, userNames)
    # End vote stage
    bookClubDB.endVoting(submissions[winner].get('id'))

    bot.send_message(message.chat.id, voteTable, parse_mode = 'html')
    bot.reply_to(message, f'The voting stage has concluded! The winner is {library.formatBookVolume(submissions[winner])}. See the vote table above to see how users voted.')


# @bot.message_handler(func = lambda m : True)
# def tester(message: telebot.types.Message):
#     print(message)
#     return


# Initialize infinity polling to enable the bot
if __name__ == '__main__':
    bot.infinity_polling()

