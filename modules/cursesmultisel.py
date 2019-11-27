#!/usr/bin/env python

import curses
import os

#options = [
#        ['aaaa', ' '],
#        ['bbbb', ' '],
#        ['cccc', ' '],
#        ['dddd', ' ']
#        ]
#
#activeopt = list()

def GetActiveOptions(options, activeopt):
    for i in range(len(options)):
        if options[i][1] == '+':
            activeopt.append(options[i][0])
        

def MainWindow(stdscr, options, activeopt):
    k = 0
    cursor_x = 0
    cursor_y = 0
    curses.start_color()
    curses.use_default_colors()

    stdscr.clear()
    stdscr.refresh()

    while 1:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if k == curses.KEY_DOWN:
            cursor_y += 1
        elif k == curses.KEY_UP:
            cursor_y -= 1
        elif k == ord(' '):
            if cursor_y > 0 and cursor_y < len(options) + 1:
                options[cursor_y-1][1] = '+' if options[cursor_y-1][1] == ' ' else ' '
        elif k > ord('0') and k < ord(str(len(options) + 1)):
            options[int(chr(k))-1][1] = '+' if options[int(chr(k))-1][1] == ' ' else ' '
        elif k == ord('\n'):
            return GetActiveOptions(options, activeopt)
        elif k == ord('q'):
            break
        
        cursor_y = max(1,cursor_y)
        cursor_y = min(len(options), cursor_y)

        title = "Selection Menu"
        
        stdscr.addstr(0,0,title + '\n')
        for i in range(len(options)):
            menuitemtext = ' ' + str(i + 1) + options[i][1] + ') ' + options[i][0]
            stdscr.addstr(menuitemtext + '\n')
        stdscr.addstr('\nq to exit    space to select    enter to continue')
        
        if (cursor_y > 0 and cursor_y < len(options) + 1):
            stdscr.move(cursor_y, 2)
        else:
            stdscr.move(cursor_y, 0)

        k = stdscr.getch()
        
def DisplayMenu(optionsorig, activeopt):
    options = list()
    for i in range(len(optionsorig)):
        options.append([optionsorig[i], ' '])
    curses.wrapper(MainWindow, options, activeopt)
