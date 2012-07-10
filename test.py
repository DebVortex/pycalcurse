import curses

def fillwin(w, c):
    y, x = w.getmaxyx()
    s = c * (x - 1)
    for l in range(y):
        w.addstr(l, 0, s)

def main(stdscr):
    stdscr.border()
    stdscr.refresh()
    stdscr.getch()

    newwin=curses.newwin(10,20,5,5)
    newwin.border()
    newwin.touchwin()
    newwin.refresh()
    newwin.getch()
    del newwin

    stdscr.touchwin()
    stdscr.refresh()
    stdscr.getch()

curses.wrapper(main)
