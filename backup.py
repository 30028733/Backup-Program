import sys
import zipfile 
#^Added to create backups: https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.open
import glob 
#^Added to scan directories: https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
import os 
#^Added to determine if a string is a directory: 
#https://stackoverflow.com/questions/8933237/how-do-i-check-if-a-directory-exists-in-python
import smtplib 
#^Added to send emails
from datetime import datetime, timedelta
#--------------------------------------------------------------------------------------------------
#Funtions to be called from main
def get_time():
    #Determine time and return for use in log
    timeUTC = datetime.now()
    #Change from UTC to AEST
    timezone = timeUTC + timedelta(hours=11)
    timedate = timezone.replace(microsecond=0)
    return timedate
#--------------------------------------------------------------------------------------------------
# append all error messages to email and send
def send_email(message):
    fileLog = open("backup.log", "a")#Must open before anything in function for logging
    emailSent = False

    email = 'To: ' + smtp["recipient"] + '\n' + 'From: ' + smtp["sender"] + '\n' + 'Subject: Backup Error\n\n'+ f"Inputted job name: {sys.argv[1]}\nDate and time of failure: {get_time()}\n" + message + '\n'
    #The below 3 lines are for testing purposes
    """
    login = 'User-' + smtp["user"] + ' Password-'+ smtp["password"]
    print(f"\nEmail Test with login: {login}")
    print(f"Email: \n{email}")
    """
    # connect to email server and send email
    try:
        smtp_server = smtplib.SMTP(smtp["server"], smtp["port"])
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        smtp_server.login(smtp["user"], smtp["password"])
        smtp_server.sendmail(smtp["sender"], smtp["recipient"], email)
        emailSent = True
        smtp_server.close()
    except Exception as error:
        print(f"FAILURE:Error email sending error: {error}")
        fileLog.write(f"\n    FAILURE: Error email sending error: {error}")
        emailSent = False
    if emailSent == True:
        print("Error email sent")
        fileLog.write(f"\n    Error email sent to: " + smtp["recipient"] + f" at {get_time()}")
    fileLog.write(f"\n    Exiting Program...")
    fileLog.close()
    sys.exit()#Ends the program after emailing as an error has occured and cannot continue
#--------------------------------------------------------------------------------------------------

def backup(backupLocation, backupDestination, logLocation, strBackupName):
    fileLog = open("backup.log", "a")#Must open before anything in function for logging
    fileLog.write(f"\n    Beginning backup: {strBackupName}")
    #Prepare for backing up
    if not os.path.isfile(backupLocation):
        if not backupLocation[len(backupLocation)-1] == "/":
            #Will cause problems if there is no / at the end of the "to backup" path, this fixes
            print(f"Adding / at {backupLocation}^(here)")
            fileLog.write(f"\n    NOTICE: Missing end / for backup directory selection.\n            Adding / at end of: {backupLocation}")
            backupLocation = backupLocation + "/"
    if not backupDestination[len(backupDestination)-1] == "/":
        #Will cause problems if there is no / at the end of the "destination" path, this fixes
        print(f"Adding / at {backupDestination}^(here)")
        fileLog.write(f"\n    NOTICE: Missing end / for destination directory selection.\n            Adding / at end of: {backupDestination}")
        backupDestination = backupDestination + "/"
    lstFiles = glob.glob(f"{backupLocation}**", recursive=True)#Had to google to figure out recursive
    n = len(lstFiles)
    lstFileNames = list()
    lstFileLocations = list()
    i = 1
    #bolEmptyFolder = False #Deprecated (checks for empty folder for console/log output)
    if i == n: #Handles singular file backup
        
        if os.path.isfile(backupLocation):
            temp1 = lstFiles[0].split("/")
            #remove root directory from string
            temp2 = temp1[len(temp1)-1]
            lstFileNames.append(temp2) #Appends end backup directory so the backup has structure
            lstFileLocations.append(lstFiles[0]) #Appends full directory for retrival
        elif os.path.isdir(backupLocation):
            print(f"Empty directory {backupLocation}, no files to backup.")
    while i < n:
        if os.path.isdir(lstFiles[i]):#if is directory then
            i +=1
            #if bolEmptyFolder:
            #    print("Empty Folder, Skipping")
            continue
        temp1 = lstFiles[i]
        #remove root directory from string
        if backupLocation in temp1:
            temp2 = temp1.replace(backupLocation, "")
        lstFileNames.append(temp2)
        lstFileLocations.append(lstFiles[i])
        i += 1
        continue
    #Attempt to create and write backup to .zip file
    if len(lstFileLocations) > 0:
        try:
            with zipfile.ZipFile(f"{backupDestination}{get_time()} backup.zip", "w") as zipBackup:
                i = 0
                n = len(lstFileLocations)
                while i < n:
                    #Allows control of how backup is structured: (Backupfile/data orginal location, arcname=Location in zip)
                    print(f"Writing {lstFileNames[i]} to {zipBackup}")
                    zipBackup.write(lstFileLocations[i], arcname=lstFileNames[i])
                    i += 1
            fileLog.write(f"\n    SUCCESS: Backup {strBackupName} completeted successfully")
        except Exception as error:#From: https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions
            print(type(error))
            print(error.args)
            print(error)
            fileLog.write(f"\n    FAILURE: Backup error: {type(error)}: {error}")
            fileLog.close()
            send_email(f"FAILURE: Backup error: {type(error)}: {error}")
    else:
        print(f"No suitable files for backup found under {backupLocation}")
        fileLog.write(f"\n    No suitable files for backup found under: {backupLocation}")
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
#Main core of program
def main():
    global smtp
    print("[Backup.py] Program Started---------------------------------------------------------------------------")
    #Config file opening/creation
    bolConfigCreate = False
    try:
        import backupcfg #trys to open an existing config file to get directory locations from
        print("Config Check?: Exists")
    except Exception as error:
        print("Config Check?: Does not exist")
        print("Unable to find backupcfg.py in program root folder")
        print("Creating backupcfg.py in program root folder")
        bolConfigCreate = True
        fileConfig = open("backupcfg.py", "x")
#--------------------------------------------------------------------------------------------------
        #Create basis for config file (was going to put in seperate function for orginisation, but caused errors)
        fileConfig.write(f"""#Backup Config File: Edit value fields to configure automated backup (CAPITAL SENSITIVE)
#Make sure lists for names, backups and destinations corespond to desired values in a column like fashion

#Backup Job names (Used to determine which directory to backup) (DON'T USE SPACES)
def backup_task_names():
    backupNames = ("backuptest","backuptest2") #(DON'T USE SPACES)
    #Replace the text inside the double quotes ("") with your backup names
    #Add more named jobs by adding commas(,) to seperate additonal jobs in double quotes ("")
    #eg: ("backupjob1name", "backupjob2name", ...)
    return backupNames
#Backup File Location (what file directory to backup)
def where_backup_files():#Defaults to the first if no name given
    backupLocations = ("ExampleFolder/ExampleFolder2/", "ExampleFolder/ExampleFile.fileExtension")
    #Replace the text inside the double quotes ("") with your files directory or file directory
    #Add more jobs by adding commas(,) to seperate additonal directories in double quotes ("")
    #eg: ("backupjob1directory", "backupjob2directory", ...)
    return backupLocations
#Backup Destination (Where the backup is stored)
def where_backup_destination():
    backupDestination = ("ExampleFolder","ExampleFolder/ExampleFolder2/")
    #Replace the text inside the double quotes ("") with your backup destination directory
    #Add more destinations by adding commas(,) to seperate additonal directories in double quotes ("")
    #eg: ("backupdestination1directory", "backupdestination2directory", ...)
    return backupDestination
#All three of the above configurables work like a table selecting just one column:
#By selecting job2 from the names the second backupLocation and backupDestination will also be selected
    
#Backup Log Location (Where the log file is created and updated)
def where_log_file():
    logDirectory = ""
    #Replace the text inside the double quotes ("") with your prefered log directory
    return logDirectory
#Error emailing details (Which email to send error reports to and to send from during automated backups)
smtp = {"sender": "example@gmail.com",          # gmail.com sender
        "recipient": "example@gmail.com",       # gmail.com recipient
        "server": "smtp.gmail.com",             # SMTP server
        "port": 587,                            # SMTP port
        "user": "example@gmail.com",            # gmail.com user
        "password": "AAAABBBBXXXXYYYYZZZZ"}     # gmail.com password
#Change the sender, recipient, user and password fields as needed
#Replace the text inside the SECOND double quotes ("":"") with required info""")
#--------------------------------------------------------------------------------------------------
        print("Config File created")
        fileConfig.close() #close after editing to prevent any possible errors from executing from open file
        import backupcfg
    #Create .log and open
    try:
        if bolConfigCreate:
            print("NOTICE: Config empty: Creating temp log at root directory. Please append a log location to config file.")
        if not os.path.isdir(backupcfg.where_log_file()):#Checks that the log directory givin is valid
            print(f"NOTICE: False directory for log file: {backupcfg.where_log_file()}")
            fileLog = open(f"backup.log", "x")
            print(f"Creating log file at root directory")
        else:    
            fileLog = open(f"{backupcfg.where_log_file()}backup.log", "x")
        print("Log File created")
        fileLog.write(f"[Backup.py] Created Log File at: {get_time()}\n[Backup.py] {get_time()} - Starting Backup Program")
    except Exception as error:
        fileLog = open("backup.log", "a")
    #Always log start of program date and time
    fileLog.write(f"\n[Backup.py] {get_time()} - Starting Backup Program")
    if bolConfigCreate: 
        #Log Config creation
        fileLog.write(f"""
    [Backup.py] Created Config File at {get_time()}
        NOTICE: Config Log directory Empty, please add log location
        FAILURE: Config File Directory Empty: Manual Intervention Required
        Exiting Program...""")
        fileLog.close()
        sys.exit()
    #Read all of the config file here
    print("Reading config...")
    smtp = backupcfg.smtp
    logLocation = backupcfg.where_log_file()
    lstBackupNames = backupcfg.backup_task_names()
    lstBackupLocation = backupcfg.where_backup_files()
    lstbackupDestination = backupcfg.where_backup_destination()
    if len(lstBackupNames) != len(lstBackupLocation) or len(lstBackupNames) != len(lstbackupDestination) or len(lstBackupLocation) != len(lstbackupDestination):
        print(f"NOTICE: Config list lengths don't match, errors could occur.")
        fileLog.write(f"\n    NOTICE: Config list lengths don't match, errors could occur.")
    #If loglocation is still empty warn user
    if logLocation == "":
        print("NOTICE: Config Log Location still empty, please add log location")
        fileLog.write("\n    NOTICE: Config Log Location still empty, please add log location")
    #If not blank check if it is false and warn user
    elif not os.path.isdir(logLocation):
        fileLog.write(f"\n    NOTICE: Configured log location invalid")
    #If errorEmail is still empty warn user
    if smtp["sender"] == "" or smtp["recipient"] == "":
        print("NOTICE: A config error email field still empty, please fill in empty field in config")
        fileLog.write("\n    NOTICE: A config error email field still empty, please fill in empty field in config")
    #Determine which job to run or run defualt if no argument is given
    strBackupLocation = ""
    bolJobMatch = False
    try:
        #Check if there is a argument if there isn't an error will occur and go to the except
        if not sys.argv[1] == "":
            i = 0
            n = len(lstBackupNames)
            try:
                #Search for input job match
                while i < n:
                    if lstBackupNames[i].lower() == str(sys.argv[1]).lower():
                        strBackupName = lstBackupNames[i]
                        strBackupLocation = lstBackupLocation[i]
                        strBackupDestination = lstbackupDestination[i]
                        bolJobMatch = True
                        break
                    i += 1
                #No named job match found error
                if bolJobMatch == False:
                    print(f"FAILURE: No configured jobs found matching: {sys.argv[1]}")
                    fileLog.write(f"\n    FAILURE: No configured jobs found matching: {sys.argv[1]}")
                    fileLog.close()
                    send_email(f"FAILURE-[Backup.py]: No configured jobs found matching: {sys.argv[1]}, please enter a job name from the config as an argument to backup > (backup.py [argument here])")
                    sys.exit()
            except Exception as error:
                #Occurs when the config has one of the lists with less items than the others and determines which is missing and reports
                print("FAILURE: Config missing critical list item")
                strError = "None"
                try:
                    strBackupDestination = lstbackupDestination[i]
                except:
                    print("")
                    strError = "BackupDestination"
                try:
                    strBackupLocation = lstBackupLocation[i]
                except:
                    print("")
                    strError = "BackupLocation"
                print(f"FAILURE: Config missing critical list item in {strError}")
                fileLog.write(f"\n    FAILURE: Config missing critical list item in {strError}")
                fileLog.close()
                send_email(f"FAILURE: Config missing critical list item in {strError}")        
    except Exception as error:
        #For automation purposes, just end program on lack of given task error
        print(f"FAILURE: No argument given")
        fileLog.write(f"\n    FAILURE: No argument given")
        fileLog.close()
        send_email(f"FAILURE-[Backup.py]: No argument given, please enter a job name from the config as an argument to backup > (backup.py [argument here])")
        sys.exit()
        #Was planning on having the user select a task if none was given but it could impact automation i removed it
        """
        while bolJobMatch == False:
            print()
            print(f"Avaliable jobs: {lstBackupNames}")
            strInput = input(f"No job selected would you like to use {lstBackupNames[0]}? [Y/N]: ").lower()#0 is the defualt as it's first
            if strInput == "n":
                print(f"Please specify ")
            elif strInput == "y":
                #Uses defualt: First in config file list
                strBackupName = lstBackupNames[0]
                strBackupLocation = lstBackupLocation[0]
                break
            else:
                continue
        """

    #Have a log for beginning backup here
    if not os.path.isdir(strBackupLocation):
        if not os.path.isfile(strBackupLocation):
            print(f"False backup location: {strBackupLocation}")
            fileLog.write(f"\n    FAILURE: False backup location: {strBackupLocation}")
            fileLog.close()
            send_email(f"FAILURE: False backup location: {strBackupLocation}, check config and file directories for mismatch")
            #Can't use absolute, must check dir then file for config error
        else:
            #Appers to write to log when closing log in order of position in code
            fileLog.close()#This writes all from this function before entering another
            #Must close then reopen files like this for each function
            backup(strBackupLocation, strBackupDestination, logLocation, strBackupName)
    else:
        fileLog.close()
        backup(strBackupLocation, strBackupDestination, logLocation, strBackupName)
    fileLog.close()
    #maybe add a log report here
    print("Finished without error\nExiting Program...")
    sys.exit()
#--------------------------------------------------------------------------------------------------
#Starts the program
if __name__ == "__main__":
    main()  
#--------------------------------------------------------------------------------------------------
