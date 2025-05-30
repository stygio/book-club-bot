# book-club-bot

This project is a Telegram bot intended as a tool for groups running book clubs. Users are able to submit books for individual sessions/meetings and then vote on them, automating the process and reducing friction.

When submitting a book, the Google Books API is queried to gather metadata, which is then used to give users a quick overview of all submissions. This feature reduces the friction introduced by requiring people to do their own research (though of course this is still possible if someone wishes to do a deep dive before voting). An example of a generated submission report can be seen in the [examples folder](./examples/). The OpenLibrary API was also considered, but ultimately Google Books simply has a larger collection (especially on an international level, i.e. non-english).

During the voting process each user gets three votes. The winner is chosen using ranked-choice (a.k.a. instant-runoff) voting with the intention of addressing the problem of users simply voting for their own books. Once the voting process is completed, a simple table is generated offering an overview of how individuals voted.

## Setup

The following steps are required to get this project up and running in your own environment. Collect the necessary tokens and IDs, then assign them to the appropriate environment variables (I personally use a `.env` file in this directory).

### Telegram

Create a Telegram bot for your book club following the steps outlined in [their documentation](https://core.telegram.org/bots#how-do-i-create-a-bot). As a result you should receive an authentication token, which this script expects to find under the `TELEGRAM_TOKEN` env. var. You will also need to enable the bot and add it to your group chat of choice.

The book club bot is set up to gate commands based on what it considers to be the master user and master chat, both of which refer to telegram IDs. These should correspond to your personal user ID in the app (`MASTER_USER_ID`) and the group chat where the bot will be used (`MASTER_CHAT_ID`). These values can be pulled by uncommenting the `tester()` message handler in [main.py](./main.py) and sending any message in a group chat with the bot present. You will find the IDs in the metadata printed to `stdout`.

### Google Books

You will need an authentication token for communicating with the Google Books API. Prepare the token per [their documentation](https://developers.google.com/books/docs/v1/using) and save it under the `GOOGLE_BOOKS_API_KEY` env. var. for the bot to use.

### Fonts

In order for `fpdf` to properly generate a submission report (especially if you want to use special symbols), you should download an appropriate font pack and place it in the [fonts folder](./fonts/). I personally used [Roboto Condensed](https://fonts.google.com/specimen/Roboto+Condensed) offered by Google. Update the file names in the `fonts` dictionary in the [constants file](./constants.py).

### Images

There are some images you can set up to customize the generated submission report. Choose images to your liking and save them in the [images folder](./images/). You will need a replacement image for when Google Books does not have a thumbnail image, an image under which the Google Books link will be embedded, and a logo for your book club. Update the file names in the `images` dictionary in the [constants file](./constants.py).
