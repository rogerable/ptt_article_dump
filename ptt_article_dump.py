#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

from telnetlib import Telnet
import pyte

# TODO: shorten long lines
#       parameterize: delay time
#       coding style checks: space around assignment
#       comment on all workarounds

ENTER = '\r'

U_MSG_MAIN_MENU_TITLE = '【主功能表】'.decode('utf-8')
U_MSG_RIGHT_DBRAC= '》'.decode('utf-8')
U_MSG_BOARD = '看板《'.decode('utf-8')
U_MSG_SEARCH_RESULT= '系列《'.decode('utf-8')
U_MSG_TIME = '時間'.decode('utf-8')
U_MSG_LINE = '行'.decode('utf-8')
U_MSG_DELETED = '本文已被刪除'.decode('utf-8')
U_MSG_NAME_SUB_WARN = '▲此頁內容會依閱讀者不同,原文未必有您的資料'.decode('utf-8')

BIG5_MSG_ANY_KEY = '請按任意鍵繼續'.decode('utf-8').encode('big5')
BIG5_MSG_LOGIN = '請輸入代號，或以 guest 參觀，或以 new 註冊:'.decode('utf-8').encode('big5')

BIG5_MSG_PASS = '請輸入您的密碼:'.decode('utf-8').encode('big5')
BIG5_MSG_WRONG_PASS = '密碼不對喔'.decode('utf-8').encode('big5')
BIG5_MSG_MULTILOGIN = '您想刪除其他重複登入的連線嗎？[Y/n]'.decode('utf-8').encode('big5')
BIG5_MSG_FAIL_LOG = '您要刪除以上錯誤嘗試的記錄嗎? [Y/n]'.decode('utf-8').encode('big5')
BIG5_MSG_MAIN_MENU_TITLE = U_MSG_MAIN_MENU_TITLE.encode('big5')
BIG5_MSG_ARTICLE_END_SIG = '(←)\x1b[30m離開'.decode('utf-8').encode('big5')
BIG5_MSG_AID = '文章代碼(AID):'.decode('utf-8').encode('big5')
BIG5_MSG_BOARD = U_MSG_BOARD.encode('big5')

POST_LIST_ENTRY_META_START = 10
AID_LEN = 9

LOGIN_TIMEOUT = 10

__all__ = ["PttArticle", "PttCon"]

class PttArticle(object):
    def __init__(self, topic, author, content, time_post, aid):
        self.topic = topic
        self.author = author
        self.content = content
        self.time_post = time_post
        self.aid = aid

# T(topic) a(author) A(AID) d(date) t(time)
    def save_article(self, output_dir=None, filename_format='TaAd'):
        import os.path

        filename = ''
        for c in filename_format:
            if filename != '' and c in 'TaAdt':
                filename = filename + '-'

            if c == 'T':
                filename = filename + self.topic.replace('/', ' ')

            elif c == 'a':
                filename = filename + self.author

            elif c == 'A':
                filename = filename + self.aid

            elif c == 'd':
                filename = filename + time.strftime('%y%m%d',
                                                    self.time_post)

            elif c == 't':
                filename = filename + time.strftime('%H%M%S',
                                                    self.time_post)

        assert filename != '', "Invalid filename format"

        if output_dir is None:
            output_dir = './'
        else:
            output_dir += '/'

        rename = 1
        while os.path.isfile(filename + '.txt'):
            filename = filename + '(' + str(rename) + ')'
            rename = rename + 1

        with open(output_dir + filename + '.txt', 'w') as f:
            f.write(self.content.encode('utf-8'))

class PttCon(object):
    def __init__(self, host=None):
        self.buf = ''
        self.cur_board = None
        self.screen = pyte.Screen(80, 24)
        self.stream = pyte.ByteStream(encodings = [("big5hkscs", "replace")])
        self.stream.attach(self.screen)
        self.tn = Telnet(host)
        self.state = "connected"

    def __del__(self):
        self.quit()

    def quit(self):
        self.send_arrow_left(6)
        self.write_like_human('\ry\r\r')
        self.state = "quitted"

    def write_like_human(self, string):
        for c in string:
            self.tn.write(c)
            time.sleep(0.1)

    def send_arrow_up(self, times=1):
        while times > 0:
            self.tn.write("\x1bOA")
            time.sleep(0.1)
            times = times - 1

    def send_arrow_down(self, times=1):
        while times > 0:
            self.tn.write("\x1bOB")
            time.sleep(0.1)
            times = times - 1

    def send_arrow_right(self, times=1):
        while times > 0:
            self.tn.write("\x1bOC")
            time.sleep(0.1)
            times = times - 1

    def send_arrow_left(self, times=1):
        while times > 0:
            self.tn.write("\x1bOD")
            time.sleep(0.1)
            times = times - 1

    def send_page_down(self, times=1, refresh=False):
        pgdown = "\x1b[6~"
        if refresh:
            pgdown = pgdown + "\x0C"
        while times > 0:
            self.tn.write(pgdown)
            time.sleep(0.1)
            times = times - 1

    def send_home(self):
        self.tn.write("\x1b[1~")
        time.sleep(0.1)

    def send_end(self):
        self.tn.write("\x1b[4~")
        time.sleep(0.1)

    def login_to_main_menu(self, login=None, password=None):
        import getpass
        self.buf = self.tn.read_until(BIG5_MSG_LOGIN)
        self.tn.write(login + ENTER)
        self.buf = self.tn.read_until(BIG5_MSG_PASS)
        if password is None:
            self.tn.write(getpass.getpass() + ENTER)
        else:
            self.tn.write(password + ENTER)

        self.buf = self.tn.read_until(BIG5_MSG_MAIN_MENU_TITLE, 1)
        login_trial = 0
        while BIG5_MSG_MAIN_MENU_TITLE not in self.buf:
            login_trial = login_trial + 1
            if login_trial > LOGIN_TIMEOUT:
                raise EOFError("login time too long")

            if BIG5_MSG_WRONG_PASS in self.buf:
                raise EOFError("Wrong password")

            if BIG5_MSG_MULTILOGIN in self.buf:
                self.tn.write('n' + ENTER)

            if BIG5_MSG_FAIL_LOG in self.buf:
                self.tn.write('n' + ENTER)

            if BIG5_MSG_ANY_KEY in self.buf:
                self.tn.write(' ')

            self.buf = self.tn.read_until(BIG5_MSG_MAIN_MENU_TITLE, 1)

        self.stream.feed(self.buf)
        self.get_data_and_feed()
        if U_MSG_MAIN_MENU_TITLE in self.screen.display[0]:
            self.state = 'main_menu'

    def go_board(self, board):
        assert self.state in ['main_menu', 'board'], \
               'go_board must be used in main_menu state'

        self.write_like_human('s' + board + ENTER)
        self.buf = self.tn.read_until(BIG5_MSG_BOARD, 0.5)
        while BIG5_MSG_BOARD not in self.buf:
            if BIG5_MSG_ANY_KEY in self.buf:
                self.tn.write(' ')

            self.buf = self.tn.read_until(BIG5_MSG_MAIN_MENU_TITLE, 1)

        self.screen.reset()
        self.stream.feed(self.buf)
        self.get_data_and_feed()

        board_menu_pattern = U_MSG_BOARD + board.lower()
        offset = self.screen.display[0].lower().find(board_menu_pattern)
        if offset != -1:
            self.state = 'board'
            end = self.screen.display[0].rfind(U_MSG_RIGHT_DBRAC)
            self.cur_board = self.screen.display[0][offset + 3 : end]

#        self.pinned_posts = 0
        self.determine_max_post()

    def determine_max_post(self):
        #TODO: use cursor-y position to do this?
        self.send_end()
        self.get_data_and_feed()
        post_num = self.screen.display[self.screen.cursor.y][1:].split()[0]

        # FIXME: This method causes problem when there are more than 100000
        # posts(e.g. ptt-Gossiping).
        while not post_num.isdigit():
#            self.pinned_post = self.penned_post + 1
            self.send_arrow_up()
            self.get_data_and_feed()
            post_num = self.screen.display[self.screen.cursor.y][1:].split()[0]

        self.refresh_page()
        post_num = self.screen.display[self.screen.cursor.y][1:].split()[0]
        self.max_post = int(post_num)

    def board_search_post(self, field, pattern):
        assert self.state in ['board', 'search'] and \
               field in ['author', 'title']
        if field == 'author':
            search_string = 'a'
        else:
            search_string = '?'
            pattern = pattern.decode('utf-8').encode('big5')

        search_string = search_string + pattern + ENTER
        self.write_like_human(search_string)
        self.get_data_and_feed(True)

        if U_MSG_SEARCH_RESULT + self.cur_board in self.screen.display[0]:
            self.state = 'search'
            self.determine_max_post()


    def parse_cursor_article(self):
        meta_off = self.screen.display[self.screen.cursor.y].find('/') - 2
        meta_str = self.screen.display[self.screen.cursor.y][meta_off:]
        meta = meta_str.split(None, 2)
        author = meta[1]
        # Raise exception when encountering a deleted post
        if '-' in author:
            raise EOFError("Deleted post")

        topic = meta[2].strip()
        time_post = time.strptime(meta[0], "%m/%d")

        self.send_arrow_right()
        self.get_data_and_feed(reset_screen=True, predecode=True)

        # Now we should in an article
        # Parse post time passively and ignore any exception
        if U_MSG_TIME in self.screen.display[2]:
            try:
                time_str = self.screen.display[2].split(None, 1)[1].strip()
                time_post = time.strptime(time_str)
            except:
                pass

        # Start dump article text
        # Always save first page
        content = ''
        for i in range(23):
            content = content + self.screen.display[i].rstrip() + '\n'

        # That bottom line shown could be assumed to be line 22 here because
        # for  multi-page articles the last line is definitely line 22 and no
        # need to do any string search
        bot_line = 22

        status_string = self.screen.display[23]
        while '100%' not in status_string:
            self.send_page_down(refresh=True)
            # erase last line
            self.get_data_and_feed(True, True, BIG5_MSG_ARTICLE_END_SIG)
            status_string = self.screen.display[23]

            bot_line_prev = bot_line
            #work around ptt name substitute warning
            while U_MSG_NAME_SUB_WARN in status_string:
                self.send_arrow_up()
                self.get_data_and_feed()
                self.write_like_human('\x0C')
                self.get_data_and_feed(True, True, BIG5_MSG_ARTICLE_END_SIG)
                status_string = self.screen.display[23]

            bot_line_start = status_string.find(u"~") + 1
            bot_line_end = status_string.find(U_MSG_LINE)
            bot_line = int(status_string[bot_line_start : bot_line_end])
            content_start = 23 - (bot_line - bot_line_prev)

            for i in range(content_start, 23):
                content = content + self.screen.display[i].rstrip() + '\n'

        # also strip trailing newline here
        content = content.rstrip('\n')

        # get aid and out
        # ptt and ptt2 display aid in different lines. Searching in buf would
        # be a lot easier.
        self.write_like_human('Q');
        self.get_data_and_feed()
        aid_off = self.buf.find(BIG5_MSG_AID)
        aid_off = self.buf.find('#', aid_off)
        aid = self.buf[aid_off : aid_off + AID_LEN]
        self.write_like_human(ENTER);
        self.get_data_and_feed(reset_screen=True)

        # create the article instance
        self.cur_article = PttArticle(topic, author, content, time_post, aid)

    def refresh_page(self, predecode=False):
    # TODO: add a last line(display[23]) non-empty detection?
        self.write_like_human('\x0C')
        self.get_data_and_feed(reset_screen=True, predecode=predecode)
        trial = 0
        while self.screen.display[23].strip() == u'':
            if trial > 2:
                break
            self.get_data_and_feed(reset_screen = False, predecode=predecode)
            trial = trial + 1

    def get_data_and_feed(self, reset_screen=False,
                          predecode=False, expect=None):
        if reset_screen:
            self.screen.reset()

        self.buf = self.tn.read_very_eager()
        t = 0
        while self.buf == '' or expect != None and expect not in self.buf:
        #FIXME: Add timeout here
            if t > 5:
                break
            time.sleep(1)
            self.buf = self.buf + self.tn.read_very_eager()
            t = t + 1

        if predecode:
            self.buf_predecode_half_esc()
        self.stream.feed(self.buf)

    def buf_predecode_half_esc(self, keep_esc=False):
        while True:
            try:
                self.buf.decode('big5hkscs')
                break
            except UnicodeDecodeError as ue:
                if self.buf[ue.end - 1] != '\x1b':
                    break
                c = self.buf[ue.start:].find('m')
                if c == -1:
                    break

                merged_char = self.buf[ue.start] + self.buf[ue.start + c + 1]
                esc_seq_str = self.buf[ue.end - 1:ue.start + c + 1]
                rest_str = self.buf[ue.start + c + 2:]
                self.buf = self.buf[:ue.start] + merged_char
                if keep_esc:
                    self.buf = self.buf + esc_seq_str
                self.buf = self.buf + rest_str

    def print_screen(self):
        for i in range(24):
            print self.screen.display[i]

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="PTT/PTT2 article dump tool.")
    parser.add_argument('-u', '--login', required=True, help='username')
    parser.add_argument('-b', '--board', required=True, help='board name')
    parser.add_argument('-a', '--search-author', help='search author')
    parser.add_argument('-t', '--search-title', help='search title')
    parser.add_argument('-r', '--range', dest='dump_range', help='dump range: \"all\" | start+amount | start-end | single')
    parser.add_argument('-o', '--output-dir', help='output directory for saving articles')
    parser.add_argument('-f', '--filename-format', default='Tad', help='filename format: [TaAdt]')
    parser.add_argument('host', default='ptt2.cc', help='host name')
    args = parser.parse_args()

    print args
    if args.dump_range is None:
        dump_range = 'last'
    else:
        if args.dump_range.isdigit():
            dump_range = [int(args.dump_range)]

        elif '+' in args.dump_range:
            r = args.dump_range.partition('+')
            dump_range = range(int(r[0]), int(r[0]) + int(r[2]))

        elif '-' in args.dump_range:
            r = args.dump_range.partition('-')
            dump_range = range(int(r[0]), int(r[2]) + 1)

        elif args.dump_range == 'all':
            dump_range = 'all'

        elif args.dump_range == 'last':
            dump_range = 'last'
        else:
            raise SyntaxError("Wrong range")

    ptt = PttCon(args.host)
    ptt.login_to_main_menu(args.login)
    ptt.go_board(args.board)

    # range: all | #start + #amount | #start - #end | #single
    if args.search_author is not None:
        ptt.board_search_post('author', args.search_author)

    if args.search_title is not None:
        ptt.board_search_post('title', args.search_title)

    print "Board %s: total %d articles in scope " % \
           (ptt.cur_board, ptt.max_post)

    if dump_range ==  'all':
        dump_range = range(1, ptt.max_post + 1)

    if dump_range ==  'last':
        print "Dump last article"
        ptt.parse_cursor_article()
        ptt.cur_article.save_article(args.output_dir)
    else:
        print "Dump from %d to %d." % (dump_range[0], dump_range[-1])
        last_dump = -1
        cnt = 0
        dumps = len(dump_range)
        for i in dump_range:
            if i > ptt.max_post:
                print str(i) + "out of range"
                break

            if i == last_dump + 1:
                ptt.send_arrow_down()

            else:
                ptt.write_like_human(str(i) + ENTER);
            ptt.get_data_and_feed()
            ptt.refresh_page()
            try:
                ptt.parse_cursor_article()
            except:
                ptt.print_screen()
                print '-----'
                print 'buf: ' + str(len(ptt.buf)) + ' bytes'
                for i in ptt.buf:
                    print hex(ord(i)),
                raise
            ptt.cur_article.save_article(args.output_dir)
            last_dump = i
            cnt = cnt + 1
            sys.stdout.write("\rDumping articles: %3d%% (%d/%d)" %
                             (cnt * 100 /dumps, cnt, dumps))
            sys.stdout.flush()

        print ", done.\n"
