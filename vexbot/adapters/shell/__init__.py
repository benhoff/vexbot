try:
    from _shim import PromptShell
    import logging
    logging.error('Please update by running `python setup.py install`')
except ImportError:
    from application import Shell as PromptShell
