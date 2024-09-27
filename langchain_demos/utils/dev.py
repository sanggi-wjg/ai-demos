from colorful_print import color


def colorful_dispatcher(c: str, msg: str, *args, **kwargs):
    dispatch = getattr(color, c)
    dispatch(msg, *args, **kwargs)


def red(msg: str, *args, **kwargs):
    colorful_dispatcher('red', msg, *args, **kwargs)


def yellow(msg: str, *args, **kwargs):
    colorful_dispatcher('yellow', msg, *args, **kwargs)


def green(msg: str, *args, **kwargs):
    colorful_dispatcher('green', msg, *args, **kwargs)


def blue(msg: str, *args, **kwargs):
    colorful_dispatcher('blue', msg, *args, **kwargs)


def magenta(msg: str, *args, **kwargs):
    colorful_dispatcher('magenta', msg, *args, **kwargs)


def cyan(msg: str, *args, **kwargs):
    colorful_dispatcher('cyan', msg, *args, **kwargs)
