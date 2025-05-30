from fpdf import FPDF, enums
from os import path

import customTypes as types
import library
import constants


dirname = path.dirname(__file__)

class SubmissionReport(FPDF):
    def __init__(self, coverImageWidth, ):
        super().__init__()
        self.coverImageWidth = coverImageWidth

    def header(self):
        # Setting font: helvetica bold 15
        self.set_font("helvetica", style="B", size=18)
        # Embed logo
        self.image(path.join(dirname, 'images', constants.images['LOGO']), x = self.l_margin, y=10, w = 10)
        # Calculating width of title and setting cursor position:
        width = self.get_string_width(self.title) + 6
        self.set_x(((210 - width) / 2) + 8)
        # Setting colors for frame, background and text:
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        # Setting thickness of the frame (1 mm)
        self.set_line_width(1)
        # Printing title:
        self.cell(
            width,
            10,
            self.title,
            border=1,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
            fill=True,
        )
        # Performing a line break:
        self.ln(15)

    # Helper function for printing cells in the chapter header
    def addChapterHeaderLine(self, text: str, newX: enums.XPos | None = None, newY: enums.YPos | None = None, cellHeight = 7, fill: bool = False):
        self.cell(
            0,
            cellHeight,
            text,
            new_x = newX if newX else "LEFT",
            new_y = newY if newY else "NEXT",
            align = "L",
            fill = fill,
        )

    def chapter_header(self, submissionId: int, bookVolume: types.BookVolume):
        # Get X, Y coordinates for image with link to Google Books page
        googleBooksLogoX = self.w - self.r_margin - 1 - 6
        googleBooksLogoY = self.get_y() + 1
        # Book title + subtitle section
        self.set_fill_color(200, 220, 255)
        self.set_font("Roboto", "B", size = 18)
        self.addChapterHeaderLine(f"({submissionId}) ", "END", "TOP", 10, True)
        self.addChapterHeaderLine(f"{bookVolume['title']}", "START", "", 10, True)
        if bookVolume['subtitle']:
            tmpX = self.get_x()
            self.set_x(self.l_margin)
            self.addChapterHeaderLine(" ", newY = "TOP", fill = True)
            self.set_x(tmpX)
            self.set_font("Roboto", "I", size = 18)
            self.addChapterHeaderLine(f"{bookVolume['subtitle']}")
        # Add image with link to Google Books page
        yAfterText = self.get_y()
        self.image(path.join(dirname, 'images', constants.images['GOOGLE_BOOKS_LINK']), x = googleBooksLogoX, y = googleBooksLogoY, h = 7, link = bookVolume['googleBooksLink'])
        self.set_y(yAfterText)
        self.ln(4)

        # Start main header section
        self.set_font("Roboto", size = 12)
        startY = self.get_y()

        # Book Cover Art
        imageHeight = 0
        if bookVolume["imageLink"]:
            imageData = self.image(bookVolume["imageLink"], x = self.l_margin, y = self.get_y(), w = self.coverImageWidth)
            imageHeight = imageData["rendered_height"]
            self.rect(x = self.l_margin, y = startY, w = self.coverImageWidth, h = imageHeight)
            self.set_x(10 + self.coverImageWidth + 6)
        else:
            imageData = self.image(path.join(dirname, 'images', constants.images['COVER_NOT_FOUND']), x = self.l_margin, y = self.get_y(), w = self.coverImageWidth)
            imageHeight = imageData["rendered_height"]
            self.rect(x = self.l_margin, y = startY, w = self.coverImageWidth, h = imageHeight)
            self.set_x(10 + self.coverImageWidth + 6)

        # Print chapter header text
        lineStartX = self.get_x()
        if bookVolume['authors']:
            self.set_x(lineStartX)
            prefixString = 'Authors: ' if len(bookVolume['authors']) > 1 else 'Author: '
            self.set_font("Roboto", "B", size=12)
            self.addChapterHeaderLine(f"{prefixString}", "END", "TOP")
            self.set_font("Roboto", size=12)
            self.addChapterHeaderLine(f"{library.formatAuthors(bookVolume['authors'])}")
        if bookVolume['categories']:
            self.set_x(lineStartX)
            self.set_font("Roboto", "B", size=12)
            self.addChapterHeaderLine("Categories: ", "END", "TOP")
            self.set_font("Roboto", size=12)
            for category in bookVolume['categories'][:6]:
                self.addChapterHeaderLine(f"\u2022 {category}")
        if bookVolume['pageCount']:
            self.set_x(lineStartX)
            self.set_font("Roboto", "B", size=12)
            self.addChapterHeaderLine("Page Count: ", "END", "TOP")
            self.set_font("Roboto", size=12)
            self.addChapterHeaderLine(f"{bookVolume['pageCount']}")

        # Set new Y position below the cover art + text based on what is longer
        self.set_y(max(self.get_y(), imageHeight + startY))
        # Performing a line break to render whitespace before the chapter body
        self.ln(4)

    def chapter_body(self, htmlText):
        self.set_font("Roboto", size=14)
        self.write_html(htmlText)
        # Performing a line break:
        self.ln(8)

    def print_chapter(self, submissionId: int, bookVolume: types.BookVolume):
        # If there is less than 90mm left in the page, create a new one
        if not (self.h - self.get_y()) > 90:
            self.add_page()
        self.chapter_header(submissionId, bookVolume)
        if bookVolume["description"]:
            self.chapter_body(bookVolume["description"])
        else:
            self.chapter_body('<b>Google Books does not have a description for this volume.</b>')


def generate(meetingId: str, submissions: dict[str, types.BookVolume]) -> str:
    # Initiailize PDF file
    report = SubmissionReport(40)
    report.set_title(f"Submissions for Meeting {meetingId} of the Wild Frog Book Club")
    report.set_author("Generated by WildFrogBookClubBot")
    report.add_page()

    # Load unicode font
    report.add_font('Roboto', '', path.join(dirname, 'fonts', constants.fonts['DEFAULT']), uni = True)
    report.add_font('Roboto', 'b', path.join(dirname, 'fonts', constants.fonts['BOLD']), uni = True)
    report.add_font('Roboto', 'i', path.join(dirname, 'fonts', constants.fonts['ITALIC']), uni = True)
    report.add_font('Roboto', 'bi', path.join(dirname, 'fonts', constants.fonts['BOLD-ITALIC']), uni = True)

    # Print a 'chapter' for each submission
    for submissionId, bookVolume in submissions.items():
        report.print_chapter(submissionId, bookVolume)

    # Save PDF file to output in local directory
    reportFilename = f"bookClubSubmissions-meeting{meetingId}.pdf"
    report.output(reportFilename)
    return reportFilename