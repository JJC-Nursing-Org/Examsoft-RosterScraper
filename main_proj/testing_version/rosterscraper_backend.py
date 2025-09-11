#!/usr/bin/env python3

# Jefferson A. Cherrington - last update: 04-17-23
# Examsoft Offline Roster Scraper v2.0, originally built for Joliet Junior College's Dept of Nursing
# Desc: converts already downloaded HTML file into CSV file,
# \\    because Examsoft does not currently have a simple export to CSV button.

# # this will be used for testing
# import PySimpleGUIQt as sGUI

# import sys

# Beautiful Soup is necessary to scan this entire HTML file
# that was downloaded offline due to Examsoft's stance on scrapers.
import bs4


class OfflineRS:
    def __init__(self):
        self.f_name = ""
        self.output_f = ""
        self.output_n = ""
        self.num_of_students = "X"
        self.full_list = "not loaded yet"
        self.e_num = ""

    # getters defined below
    def get_inp_name(self):  # unlikely call
        return self.f_name

    def get_exp_name(self):  # unlikely call
        return self.output_n

    def get_exp_folder(self):  # unlikely call
        return self.output_f

    def get_num_stu(self):
        return self.num_of_students

    def get_all_stu(self):
        return self.full_list

    # setters defined below:
    def set_inp_name(self, x):
        self.f_name = x

    def set_exp_name(self, x):
        self.output_n = x

    def set_exp_folder(self, x):
        self.output_f = x

    def set_num_stu(self, x):
        self.num_of_students = x

    def set_all_stu(self, x):
        self.full_list = x

    def run_scraper(self):
        html_file_to_import = self.get_inp_name()
        # in v2, all of these file paths will go from hardcoded to a GUI - should be coded to support macOS

        csv_to_exportRAW = self.get_exp_folder() + "/" + self.get_exp_name() + "_raw.csv"
        csv_to_exportFINE = self.get_exp_folder() + "/" + self.get_exp_name() + "_fine.csv"

        # this segment puts the raw HTML file into Beautiful Soup to be parsed.
        with open(html_file_to_import) as fp:
            soup = bs4.BeautifulSoup(fp, 'html.parser')

        # I am using this to shorten my search.
        # knowing that every piece of data is hidden inside a "grid row" styled HTML div,
        # I use bs4 to find the HTML class
        bowl = soup.find_all("div", class_="grid-row__content grid-row__selectable")

        # cute little counter that tells me what my final count should be
        how_many_students = str(len(bowl)) + " students loaded."
        print(how_many_students)

        self.set_num_stu(how_many_students)
        # TODO: remove this debug.
        print("This is the number of students being printed out after set_num_stu was called: " + self.get_num_stu())

        # initializes every array for the named "columns" of future data
        lastName = []
        firstName = []
        stuID = []
        stuStatusCurrent = []
        stuStatusInvite = []
        stuEmail = []
        stuInviteDate = []
        stuLastLogin = []
        stuLastReg = []
        stuLabUser = []
        stuNonSec = []
        stuTimeMult = []

        # these are our meta counters.
        # we use full_record like a spoon in a bowl of soup:
        # ...grab what you need, suck it up, then go back for more until there is nothing left in the bowl
        full_record = []

        # mass_record in this analogy is our stomach, that stores EVERYTHING from the bowl.
        mass_record = []

        for i in range(len(bowl)):
            for string in bowl[i].strings:
                if string != "\n":
                    finalStr = string.strip()  # this attempts to get rid of random spaces in my actual data elems
                else:
                    finalStr = ""  # this forces bad data to be nothing
                full_record.append(finalStr)

            mass_record.append(full_record)  # this is where our RAW csv is populated.

            lastName.append(full_record[1])
            firstName.append(full_record[3])
            stuID.append(full_record[5])

            # looks at multiple fields / data elems, combines them into a single field, and rips away the extra spaces
            nStatus = (full_record[10] + full_record[11] + full_record[12] + full_record[13] + full_record[14]).strip()

            stuStatusCurrent.append(nStatus)

            # this section is set up to cover all the edge cases I've run into so far - see my reasoning in that Excel
            # document but also remember the off-by-one (subtract one from the column)
            # numbering when looking at columns / aka the "magic numbers"

            if full_record[36] == "Non-Secure":  # edge case: student IS Lab User, IS Non-Secure
                stuEmail.append(full_record[18])
                stuInviteDate.append(full_record[23])
                stuStatusInvite.append("")
                stuLastLogin.append(full_record[27])
                stuLastReg.append(full_record[29])
                stuLabUser.append(full_record[32])
                stuNonSec.append(full_record[36])
                stuTimeMult.append(full_record[39])
            elif full_record[32] == "Lab User":  # edge case: student IS Lab User, NOT Non-Secure
                stuEmail.append(full_record[18])
                stuInviteDate.append(full_record[23])
                stuStatusInvite.append("")
                stuLastLogin.append(full_record[27])
                stuLastReg.append(full_record[29])
                stuLabUser.append(full_record[32])
                stuNonSec.append(full_record[34])
                stuTimeMult.append(full_record[38])
            elif full_record[35] == "Non-Secure":  # edge case: student HAS TimeMult, IS NOT Lab User, IS Non-Secure
                stuEmail.append(full_record[18])
                stuInviteDate.append(full_record[23])
                stuStatusInvite.append("")
                stuLastLogin.append(full_record[27])
                stuLastReg.append(full_record[29])
                stuLabUser.append(full_record[32])
                stuNonSec.append(full_record[35])
                stuTimeMult.append(full_record[38])
            elif nStatus.strip() == "Needs Invite":  # edge case: student IS NOT Lab User AND needs Invite
                stuEmail.append(full_record[20])
                stuStatusInvite.append(full_record[25].strip())
                stuInviteDate.append("")
                stuLastLogin.append("")
                stuLastReg.append("")
                stuLabUser.append(full_record[35])
                stuNonSec.append(full_record[38])
                stuTimeMult.append(full_record[41])
            elif nStatus.strip() == "Invite Expired":  # edge case: student MAY be Lab User
                stuEmail.append(full_record[18])
                stuInviteDate.append(full_record[23])
                stuStatusInvite.append("")
                stuLastLogin.append("")
                stuLastReg.append("")
                stuLabUser.append(full_record[31])
                stuNonSec.append(full_record[37])
                stuTimeMult.append(full_record[40])
            # elif full_record[37] == "150%":        # edge case: student HAS TimeMult, IS Lab User
            #       stuEmail.append(full_record[18])
            #       stuInviteDate.append(full_record[23])
            #       stuStatusInvite.append("")
            #       stuLastLogin.append(full_record[27])
            #       stuLastReg.append(full_record[29])
            #       stuLabUser.append(full_record[32])
            #       stuNonSec.append(full_record[34])
            #       stuTimeMult.append(full_record[37])

            else:
                stuEmail.append(full_record[18])
                stuInviteDate.append(full_record[23])
                stuStatusInvite.append("")
                stuLastLogin.append(full_record[27])
                stuLastReg.append(full_record[29])
                stuLabUser.append(full_record[32])
                stuNonSec.append(full_record[34])
                stuTimeMult.append(full_record[37])

            full_record = []  # after consuming the data, we must rinse the "spoon" off in order to eat again

        # this provides a cute little printout of the data being exported.

        full_list = ""

        for i in range(len(bowl)):

            self.e_num = ""

            if i == 0:
                self.e_num = "Entry #1:\n"
            else:
                self.e_num = "\n\nEntry #{}:\n".format(str(i + 1))

            full_list = full_list \
                        + self.e_num \
                        + "\tLast Name: {}\n" \
                          "\tFirst Name: {}\n" \
                          "\tStudent ID: {}\n" \
                          "\tStatus [Active]: {}\n" \
                          "\tStudent Email: {}\n" \
                          "\tDate Invited: {}\n" \
                          "\tLast Login: {}\n" \
                          "\tLast Registered: {}\n" \
                          "\tLab User: {}\n" \
                          "\tNon-Secure User: {}\n" \
                          "\tTime Multiplier: {}\n".format(
                lastName[i], firstName[i], stuID[i], stuStatusCurrent[i], stuEmail[i],
                stuInviteDate[i], stuLastLogin[i], stuLastReg[i], stuLabUser[i], stuNonSec[i], stuTimeMult[i])

            print("\n\nEntry #{}:\n"
                  "\tLast Name: {}\n"
                  "\tFirst Name: {}\n"
                  "\tStudent ID: {}\n"
                  "\tStatus [Active]: {}\n"
                  "\tStudent Email: {}\n"
                  "\tDate Invited: {}\n"
                  "\tLast Login: {}\n"
                  "\tLast Registered: {}\n"
                  "\tLab User: {}\n"
                  "\tNon-Secure User: {}\n"
                  "\tTime Multiplier: {}\n".format(
                str(i + 1), lastName[i], firstName[i], stuID[i], stuStatusCurrent[i], stuEmail[i],
                stuInviteDate[i], stuLastLogin[i], stuLastReg[i], stuLabUser[i], stuNonSec[i], stuTimeMult[i]))

        self.set_all_stu(full_list)

        # this is a RAW dump, delimited by semicolons.
        # Column Name isn't included as edge cases are discovered in this mess
        with open(csv_to_exportRAW, "w") as rawFile:
            for row in mass_record:
                for x in row:
                    rawFile.write(x + ";")
                rawFile.write("\n")

        rawFile.close()
        print("Raw File has been successfully written.")

        # TODO: replace this sGUI with a QT variant.
        # sGUI.popup_ok("Raw File has been successfully written.")

        # this is the proper export, delimited by semicolons.
        # Reusing mass_record to avoid having to touch a bs4 obj unnecessarily (bowl)
        with open(csv_to_exportFINE, "w") as goodFile:
            goodFile.write("Last Name; First Name; Student ID; Status; Student Email; Date Invited;"
                           "Last Login; Last Registered; Lab User; Non-Secure User; Time Multiplier; Action\n")
            for y in range(len(mass_record)):
                goodFile.write("{}; {}; {}; {}; {}; {}; {}; {}; {}; {}; {}; {}\n"
                               .format(lastName[y], firstName[y], stuID[y], stuEmail[y],
                                       stuStatusCurrent[y], stuInviteDate[y], stuLastLogin[y], stuLastReg[y],
                                       stuLabUser[y], stuNonSec[y], stuTimeMult[y], stuStatusInvite[y]))

        goodFile.close()
        print("Good File has been successfully written.")

        # TODO: replace this sGUI with a QT variant.
        # sGUI.popup_ok("Good File has been successfully written.")

        return True


# def my_gui_creator():
    # sGUI.theme('Dark2')
    #
    # if len(sys.argv) == 1:
    #     event, values = sGUI.Window('Import Examsoft HTML File',
    #                                 [[sGUI.Text('Document to open')],
    #                                  [sGUI.In(), sGUI.FileBrowse()],
    #                                  [sGUI.Open(), sGUI.Cancel()]]).read(close=True)
    #     f_name = values[0]
    # else:
    #     f_name = sys.argv[1]
    #
    # if not f_name:
    #     sGUI.popup_error("Cancelling: no filename supplied.", title="Program Exiting Now.")
    #     raise SystemExit("Cancelling: no filename supplied")
    # else:
    #     sGUI.popup('The filename you chose was: ', f_name)
    #
    # output_place = sGUI.popup_get_folder("Output Folder for CSV's:")
    # output_name = sGUI.popup_get_text("Name your CSV's:")

    # run_scraper(f_name, output_place, output_name)

# def main():
# my_gui_creator()


# main()
