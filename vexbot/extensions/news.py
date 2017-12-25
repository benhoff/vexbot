import logging

import gensim
import newspaper


def summarize_article(self, url: str, *args, **kwargs):
    article = newspaper.Article(url)
    article.download()
    article.parse()
    summarization = gensim.summarization.summarize(article.text)
    return summarization


def get_hot_trends(self, *args, **kwargs):
    return newspaper.hot()


def get_popular_urls(self, *args, **kwargs):
    return newspaper.popular_urls()
