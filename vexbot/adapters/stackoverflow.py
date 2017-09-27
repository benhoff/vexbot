from os import path

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# NOTE: This is just a stub! Currently not finished!
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(chrome_options=options)

driver.get('https://chat.stackoverflow.com/rooms/6/python')

comment_block = driver.find_element_by_id('chat')
comments = comment_block.find_elements_by_class_name('user-container')
num_comments = len(comments)
print(num_comments)
for comment in comments:
    username = comment.find_element_by_class_name('username').text
    messages = comment.find_elements_by_class_name('messages')
    texts = []
    for message in comment.find_elements_by_class_name('message'):
        texts.append(message.find_element_by_class_name('content').text)
    print('{}: {}'.format(username, texts.pop(0)))
    for t in texts:
        print('    {}'.format(t))


driver.close()
driver.quit()
