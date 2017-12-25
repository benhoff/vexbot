from os import path
from time import sleep

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from vexbot.adapters.messaging import Messaging


class StackOverflow:
    def __init__(self, room='https://chat.stackoverflow.com/rooms/6/python'):
        options = Options()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.get(room)
        self.messaging = Messaging('stack')

    def run(self):
        # start messaging
        self.messaging._setup()
        # Get the chat block
        comment_block = self.driver.find_element_by_id('chat')
        # Get the comments from the chat block
        comments = comment_block.find_elements_by_xpath('//*[@id="chat"]')
        # calculate the number of comments
        num_comments = len(comments)
        # get the last comment
        last_comment = comments[-1]
        last_message_length = len(last_comment.find_elements_by_class_name('message'))
        while True:
            comments = comment_block.find_elements_by_xpath('//*[@id="chat"]')
            # Check last one here
            messages = last_comment.find_elements_by_class_name('message')
            message_length = len(messages)
            if message_length > last_message_length:
                username = last_comment.find_elements_by_class_name('username')[-1].text
                messages = messages[last_message_length - message_length:]
                texts = []
                for message in messages:
                    texts.append(message.find_element_by_class_name('content').text)
                text = '\n'.join(texts)
                self.messaging.send_chatter('stack', author=username, message=text, channel='stackoverflow')
                last_message_length = message_length

            new_num = len(comments)
            if new_num > num_comments:
                delta = num_comments - new_num
                for comment in comments[delta:]:
                    username = comment.find_element_by_class_name('username').text
                    messages = comment.find_elements_by_class_name('messages')
                    texts = []
                    for message in comment.find_elements_by_class_name('message'):
                        texts.append(message.find_element_by_class_name('content').text)
                    text = '\n'.join(texts)
                    self.messaging.send_chatter('stack', author=username, message=text, channel='stackoverflow')
                # loop maintainence 
                num_comments = new_num
                last_comment = comments[-1]
                last_message_length = len(last_comment.find_elements_by_class_name('message'))
            else:
                sleep(1)

    def __del__(self):
        try:
            self.driver.close()
            self.driver.quit()
        except Exception:
            pass


def main():
    s = StackOverflow()
    s.run()


if __name__ == '__main__':
    main()
