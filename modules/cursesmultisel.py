#!/usr/bin/env python

import curses
import curses.textpad
import os

options = [
        ['aaaa', 'sw',  ' '],
        ['bbbb', 'txt', 'some text'],
        ['cccc', 'sw',  ' '],
        ['dddd', 'sw',  ' ']
        ]

activeopt = list()

def GetActiveOptions(options, activeopt):
    for i in range(len(options)):
        if options[i][1] == 'sw':
            if options[i][2] == '+':
                activeopt.append(options[i][0])
        elif options[i][1] == 'txt' and options[i][2]:
            activeopt.append([options[i][0], options[i][2]])

def Enter_Is_Terminate(k):
    if  k == 10: # enter
        k = 7   # terminate
    return k

def TextBoxWindowForOption(win_y, menuitemtext):
    textboxwindow = curses.newwin(1, curses.COLS, win_y, len(menuitemtext))
    box = curses.textpad.Textbox(textboxwindow)
    box.edit(Enter_Is_Terminate)
    inputstr = box.gather()
    return(inputstr)

def MainWindow(stdscr, options, activeopt):
    k = 0
    cursor_x = 0
    cursor_y = 0
    curses.start_color()
    curses.use_default_colors()

    stdscr.clear()
    stdscr.refresh()

    title = "Selection Menu\n"
    selector_y = 2

    while 1:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if k == curses.KEY_DOWN:
            cursor_y += 1
        elif k == curses.KEY_UP:
            cursor_y -= 1

        elif k == ord(' '):
            if cursor_y > 0 and cursor_y < len(options) + 2:

                if options[cursor_y - selector_y][1] == 'sw':
                    options[cursor_y - selector_y][2] = '+' if options[cursor_y - selector_y][2] == ' ' else ' '

                elif options[cursor_y - selector_y][1] == 'txt':
                    menuitemtext = 'txt ' + str(cursor_y) + ' ) ' + options[cursor_y - selector_y][0] + ' | '
                    inputstr = TextBoxWindowForOption(cursor_y, menuitemtext)
                    options[cursor_y - selector_y][2] = inputstr

        elif k > ord('0') and k < ord(str(len(options) + 1)):
            if options[int(chr(k)) - 1][1] == 'sw':
                options[int(chr(k)) - 1][2] = '+' if options[int(chr(k)) - 1][2] == ' ' else ' '
            elif options[int(chr(k)) - 1][1] == 'txt':
                menuitemtext = 'txt ' + str(chr(k)) + ' ) ' + options[int(chr(k)) - 1][0] + ' | '
                inputstr = TextBoxWindowForOption(int(chr(k)) + selector_y - 1, menuitemtext)[:-1]
                options[int(chr(k)) - 1][2] = inputstr

        elif k == ord('\n'):
            return GetActiveOptions(options, activeopt)
        elif k == ord('q'):
            break
        
        cursor_y = max(selector_y, cursor_y)
        cursor_y = min(len(options) + 1, cursor_y)

        
        stdscr.addstr(0,0,title + (selector_y - 1) * '\n')

        for i in range(len(options)):
            if options[i][1] == 'sw':
                menuitemtext = '    ' + str(i + 1) + options[i][2] + ') ' + options[i][0]
            elif options[i][1] == 'txt':
                menuitemtext = 'txt ' + str(i + 1) + ' ) ' + options[i][0] + ' | ' + options[i][2]
            else:
                menuitemtext = 'ERROR'
            stdscr.addstr(menuitemtext + '\n')
        stdscr.addstr('\nq to exit    space to select    enter to continue')
        
        if (cursor_y > (selector_y - 1) and cursor_y < len(options) + selector_y):
            stdscr.move(cursor_y, 5)
        else:
            stdscr.move(cursor_y, 0)

        k = stdscr.getch()

        
def DisplayMenu(optionsorig, activeopt):

    options = list()
    for i in range(len(optionsorig)):
        if optionsorig[i][1] == 'sw':
           options.append([optionsorig[i][0], 'sw', ' '])
        elif optionsorig[i][1] == 'txt':
            options.append([str(optionsorig[i][0]), 'txt', str(optionsorig[i][2])])

    curses.wrapper(MainWindow, options, activeopt)

if __name__ == "__main__":
    DisplayMenu(options, activeopt)
    print(activeopt)
