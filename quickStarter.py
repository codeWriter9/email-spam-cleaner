"""Shows basic usage of the Gmail API.
Pulls The list of N emails
For each email checks against a list of spam email addresses
If Spam then deletes
else skips
"""
from __future__ import print_function
import argparse
import pickle
import os.path
import sys
import re
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class QuickStart:
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        self.GLOBAL_SPAM_LIST = []
        self.GLOBAL_CACHE = []
        self.MAXIMUM_MESSAGES_TO_BE_LOADED = 20
        self.userId = 'me'
        self.significat_digits = '.2f'
        self.id_str = 'id'
        self.payload = 'payload'
        self.headers = 'headers'
        self.labelIds = 'labelIds'
        self.value = 'value'        
        self.skipped_emails = []
        self.total_msgs_trashed = []
        self.total_msgs_skipped = []
        
        
    def self_check(self):
        print("Hello World!")
        
    def run(self):
        arguments_tuple = self.load_arguments()
        self.start = time.time()
        print("=======Connecting==To===Server=====")
        self.service = build('gmail', 'v1', credentials=self.creds())
        
        #Call GMail API
        results = self.list_messages()
        messages = results.get('messages', [])
        self.save_loaded_messages(messages)
        fetch_time_taken = time.time() - self.start
        print("\n Message Ids Fetched (seconds): " + format(fetch_time_taken, self.significat_digits))
        
        # process
        self.process_messages(messages)
        # save 
        self.save_skipped_emails(self.skipped_emails)
        # print stats
        self.print_stats();
        
        
    
    def print_stats(self):    
        print("\n Total Messages Trashed: " + str(len(self.total_msgs_trashed)))
        print("\n Total Messages Skipped: " + str(len(self.total_msgs_skipped)))        
        time_taken = time.time() - self.start
        print("\n Time Taken (seconds): " + format(time_taken, self.significat_digits)) 
        print("\n\n\n")
        print("=======Program==Will===Exit=====")
        print("=======Bye======================")
        
        
    def extract_email(self, raw_email):
        email_list = raw_email.split(' ')
        return re.sub('[^a-zA-Z0-9-_*.@_]', '', email_list[len(email_list) - 1])

    def is_from(self, header):
        return header['name'] == 'From'

    def to_be_trashed(self, labels):
        return 'IMPORTANT' not in labels and 'SENT' not in labels    
        
    def list_messages(self):
        return self.service.users().messages().list(userId=self.userId, maxResults=self.MAXIMUM_MESSAGES_TO_BE_LOADED).execute()
        
    def get_message(self, message):
        return self.service.users().messages().get(userId=self.userId, id=message[self.id_str]).execute()

    def trash_message(self, message):
        return self.service.users().messages().trash(userId=self.userId, id=message[self.id_str]).execute()        
        
    def not_in_cache(self, message):
        return message['id'] not in self.GLOBAL_CACHE
        
    def process_messages(self, messages):
        if messages:
            for message in messages:
                if self.not_in_cache(message):
                    try:                        
                        msg_body = self.get_message(message)
                        headers, labels = msg_body[self.payload][self.headers], msg_body[self.labelIds]                        
                        self.process_headers(message, headers, labels)
                    except  Exception as exception:
                        print(type(exception))
                        continue
                    

        
    def process_headers(self, message, headers, labels):        
        for header in headers:            
            if self.is_from(header) and self.to_be_trashed(labels):
                email = self.extract_email(header['value'])
                if email in self.GLOBAL_SPAM_LIST:
                    print("Trashing Message: " + str(message['id']) + " :from: " + str(email))
                    try:
                        trash_response = self.trash_message(message)
                        print("Trashed: " + str(message['id']) + " :Response: " + str(trash_response))
                        self.total_msgs_trashed.append("Trashed: " + str(message['id']) + " :Response: " + str(trash_response))
                    except Exception as exception:
                        print(type(exception))
                        continue
                else:
                    try:
                        print("\tSkipping Message:" + " :from: " + str(email))
                        print("\t" + str(msg_body['labelIds']) + ":" + str(msg_body['snippet']))
                        self.total_msgs_skipped.append(" :from: " + str(email) + "\t" + str(msg_body['labelIds']) + ":" + str(msg_body['snippet']))
                        self.skipped_emails.append(str(email))
                    except Exception as exception:
                        print(type(exception))
                        continue
                                
                            
                            
                            
    
    """ load arguments from command line
    """        
    def load_arguments(self):
        print("=======loading==arguments=====")
        res = []
        parser = argparse.ArgumentParser()
        parser.add_argument("spam_email_list", help="provide spam email list")
        args = parser.parse_args()
        print(args)
        if args.spam_email_list and os.path.exists(args.spam_email_list):
            print(args.spam_email_list)
            with open(args.spam_email_list, 'r') as spam_list_file:
                for line in spam_list_file:
                    res.append(line)
        print("=======loaded====SPAM=LIST=====")    
        res = sorted(res)
        for email in res:
            self.GLOBAL_SPAM_LIST.append(email.replace("\n", ""))
        print(self.GLOBAL_SPAM_LIST)
        text_file = open("sorted-spam.txt", "w")
        n = text_file.write(str("\n".join(sorted(set(self.GLOBAL_SPAM_LIST)))))
        text_file.close()
        print("=======saved====SPAM=LIST=====")
        print()
        print("=======loading====cache=LIST=====")
        res = []
        if os.path.exists("cache-messages.txt"):
            print("cache-messages.txt")
            with open("cache-messages.txt", 'r') as cache:
                for line in cache:
                    res.append(line)
        for message_id in res:
            self.GLOBAL_CACHE.append(message_id.replace("\n", ""))
        print(self.GLOBAL_CACHE)
        print("=======loaded====cache=LIST=====")
        return ()
        
        
    """ The file token.pickle stores the user's access and refresh tokens, and is
    created automatically when the authorization flow completes for the first
    time."""    
    def creds(self):
        print("=======Verifying====Credentials=====")
        creds = None        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)    
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        print("=======VERIFIED=====================")
        return creds
        
    def save_loaded_messages(self, a_list):
        text_file = open("cached-mesages.txt", "w")
        for k in a_list:
            text_file.write("{}\n".format(k['id']))
        text_file.close()
        
    def save_skipped_emails(self, a_list):
        text_file = open("skipped-emails.txt", "w")
        n = text_file.write(str("\n".join(sorted(set(a_list)))))
        text_file.close()




if __name__ == '__main__':
    quick_start = QuickStart()
    quick_start.run()