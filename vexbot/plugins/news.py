import logging

import gensim
import newspaper

from vexbot.command import command


@command
def do_summarize_article(self, url: str, *args, **kwargs):
    article = newspaper.Article(url)
    article.download()
    article.parse()
    summarization = gensim.summarization.summarize(article.text)
    return summarization


@command
def do_get_hot_trends(self, *args, **kwargs):
    return newspaper.hot()


@command
def do_get_popular_urls(self, *args, **kwargs):
    return newspaper.popular_urls()
