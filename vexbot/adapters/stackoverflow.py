from os import path
from time import sleep

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from vexbot.adapters.messaging import Messaging
from vexbot.adapters.scheduler import Scheduler


class StackOverflow:
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.get('https://chat.stackoverflow.com/rooms/6/python')
        self.messaging = Messaging('stack')

    def run(self):
        self.messaging.start()
        comment_block = self.driver.find_element_by_id('chat')
        comments = comment_block.find_elements_by_class_name('user-container')
        num_comments = len(comments) - 1
        while True:
            comments = comment_block.find_elements_by_class_name('user-container')
            new_num = len(comments)
            print(new_num, num_comments)
            if new_num > num_comments:
                delta = new_num - num_comments
                print('this is dle', delta)
                for comment in comments[:delta]:
                    username = comment.find_element_by_class_name('username').text
                    messages = comment.find_elements_by_class_name('messages')
                    texts = []
                    for message in comment.find_elements_by_class_name('message'):
                        texts.append(message.find_element_by_class_name('content').text)
                    text = '\n'.join(texts)
                    self.messaging.send_chatter('stack', author=username, message=text)
                # loop maintainence 
                num_comments = new_num
            else:
                print('sleep')
                sleep(1)

    def __del__(self):
        self.driver.close()
        self.driver.quit()

def main():
    s = StackOverflow()
    s.run()

if __name__ == '__main__':
    main()
