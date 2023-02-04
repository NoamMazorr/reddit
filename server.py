from select import select
from socket import *
from datetime import date
from reddit.keywords import keywords
import reddit.db as db
import better_profanity as bp
import re, pickle, _thread, time, reddit, base64


class server:
    def __init__(self):
        # connect to database tables. 
        self.subr_db = db.subr()
        self.post_db = db.post()
        self.comment_db = db.comment()
        self.keyword_db = db.keyword_db()
        self.ip_ban_db = db.ip_bans()
        self.user_ban_db = db.user_bans()
        self.settings_db = db.settings()

        _thread.start_new_thread(self.check_delete_subreddit, ())


    def check_delete_subreddit(self):
        ''' 
        check if subreddit is not active. if it is delete all subr content from db
        '''
        while True:
            communities = self.subr_db.get_all_communities()
            for comm in communities:
                # check if subr wasnt active over a certain duration
                if time.time() - comm['last_active_time'] > 3456.0:
                    
                    # delete comments by posts in subreddit
                    posts = self.post_db.get_posts_by_subr_id(self.subr_db.get_subr_id(comm['name']))
                    for p in posts:
                        self.comment_db.delete_comments_by_post_id(p['_id'])

                    # delete subreddit posts and subreddit
                    self.post_db.delete_posts_by_subr_id(self.subr_db.get_subr_id(comm['name']))
                    self.keyword_db.delete_many_by_subr_id(comm['_id'])
                    self.subr_db.delete_community(comm['name'])


    def send_post(self, sockobj, post_id):
        ''' 
        send post information to socketobj
        '''
        comments = self.comment_db.get_comments_by_post_id(post_id)
        main_post = self.post_db.get_post_by_id(post_id)

        # organize data
        if main_post['is_img']:
            with open(main_post["content"], 'rb') as obj:
                img = base64.b64encode(obj.read()).decode()
            main_post['content'] = img
        
        st = f'discussion:{str(main_post)}'
        if comments:
            for com in comments:
                st += f';{str(com)}'
                
        # add length of data so client can recieve over buffer
        st = str(len(st + str(len(st)))) + st
        sockobj.send(st.encode())


    def remove_user_in_subr(self, user):
        # remove user from self.users_in_subr dict
        for key1, val1 in dict(self.users_in_subr).items():
            if user in val1:
                self.users_in_subr[key1].remove(user)


    def run_server(self):
        addr = '172.18.64.1'
        BUFF = 4096

        server_sock = socket(AF_INET, SOCK_STREAM)

        # bind server
        server_sock.bind((addr, 11111))
        port = server_sock.getsockname()[1]

        server_sock.listen(2)

        readsocks = [server_sock]
        writesocks = []

        self.users_in_subr = {}     # {subreddit: users list} dict. stores usernames or ips of users in a certain subreddit
        user_time_in_subr = {}     # {user: time} dict for time user visits subreddit
        user_ip = {}     # {user: socket} dict

        bp.profanity.load_censor_words()     # load words for profanity detection
        self.settings = self.settings_db.get_settings()     # get current algorithm settings from db

        while True:
    
            # select sockets for reading and writing
            readables, writeables, exceptions = select(readsocks, writesocks, [])

            # add new subreddits to {subreddit: users} dictionary
            for com in self.subr_db.get_all_communities():
                if com['name'] not in self.users_in_subr:
                    self.users_in_subr[com['name']] = []

            for sockobj in readables:

                try:
                    # add new socket
                    if sockobj is server_sock:
                        newsock, address = sockobj.accept()

                        print('Connect:', address, id(newsock))

                        # if socket is of a banned ip dont communicate with it else add it to readsocks and writesocks
                        if newsock.getpeername()[0] in self.ip_ban_db.get_all_ip():
                            newsock.send('banned'.encode())
                            newsock.close()
                        else:
                            readsocks.append(newsock)
                            writesocks.append(newsock)
                    else:
                        #recieve client data
                        data = sockobj.recv(BUFF).decode()

                        if re.match(r'get:subr:r/(.+)', data):
                            try:
                                data_lst = data.split(':')
                                community = self.subr_db.get_community(data_lst[2][2:])
                                user = data_lst[3]  # might cause IndexError

                                user_time_in_subr[user] = time.time()

                                # remove user from previous subreddit
                                for subr in self.users_in_subr:
                                    if user in self.users_in_subr[subr]:
                                        self.users_in_subr[subr].remove(user)

                                self.users_in_subr[community['name']].append(user)
                                
                            # in case user is not logged in. data wont have username in the end
                            except IndexError:
                                m_obj = re.match(r'get:subr:r/(.+)', data)
                                community = self.subr_db.get_community(m_obj.group(1))
                                client_ip = sockobj.getpeername()[0]

                                user_time_in_subr[client_ip] = time.time()

                                # remove ip from previous subreddit
                                for subr in self.users_in_subr:
                                    if client_ip in self.users_in_subr[subr]:
                                        self.users_in_subr[subr].remove(client_ip)

                                self.users_in_subr[community['name']].append(client_ip)

                            st = f'subr_page:{community["name"]}:{community["description"]}:{community["_id"]}:{community["date"]}'

                            posts = self.post_db.get_posts_by_subr_id(self.subr_db.get_subr_id(community["name"]))
                            for p in posts:
                                if not p["is_img"]:
                                    # text post
                                    st += f';{p["_id"]}:{p["is_img"]}:{p["user"]}:{p["title"]}:{p["content"]}:{p["date"]}'
                                else:
                                    # read image then b64encode to send as string
                                    with open(p["content"], 'rb') as obj:
                                        img = base64.b64encode(obj.read())
                                    st += f';{p["_id"]}:{p["is_img"]}:{p["user"]}:{p["title"]}:{img.decode()}:{p["date"]}'

                            # add data length
                            st = str(len(st + str(len(st)))) + st

                            sockobj.send(st.encode())

                        elif re.match(r'get:subr:(.+)(:.+)?', data):

                            if re.match(r'get:subr:(\d+)(:.+)?', data) and self.subr_db.get_community_by_id(int(re.match(r'get:subr:(\d+)(:.+)?', data).group(1))):
                                # send subreddit if search is by id
                                try:
                                    data_lst = data.split(':')
                                    community = self.subr_db.get_community_by_id(int(data_lst[2]))
                                    user = data_lst[3]  # might cause IndexError

                                    user_time_in_subr[user] = time.time()

                                    # remove user from previous subreddit
                                    for subr in self.users_in_subr:
                                        if user in self.users_in_subr[subr]:
                                            self.users_in_subr[subr].remove(user)

                                    self.users_in_subr[community['name']].append(user)

                                # in case user is not logged in. data wont have username in the end
                                except IndexError:
                                    m_obj = re.match(r'get:subr:(\d+)(:.+)?', data)
                                    community = self.subr_db.get_community_by_id(int(m_obj.group(1)))
                                    client_ip = sockobj.getpeername()[0]

                                    user_time_in_subr[client_ip] = time.time()

                                    # remove ip from previous subreddit
                                    for subr in self.users_in_subr:
                                        if client_ip in self.users_in_subr[subr]:
                                            self.users_in_subr[subr].remove(client_ip)

                                    self.users_in_subr[community['name']].append(client_ip)

                                st = f'subr_page:{community["name"]}:{community["description"]}:{community["_id"]}:{community["date"]}'

                                posts = self.post_db.get_posts_by_subr_id(self.subr_db.get_subr_id(community["name"]))
                                for p in posts:
                                    if not p["is_img"]:
                                        # text post
                                        st += f';{p["_id"]}:{p["is_img"]}:{p["user"]}:{p["title"]}:{p["content"]}:{p["date"]}'
                                    else:
                                        # read image then b64encode to send as string
                                        with open(p["content"], 'rb') as obj:
                                            img = base64.b64encode(obj.read())
                                        st += f';{p["_id"]}:{p["is_img"]}:{p["user"]}:{p["title"]}:{img.decode()}:{p["date"]}'

                                # add data length
                                st = str(len(st + str(len(st)))) + st

                                sockobj.send(st.encode())
                                
                            # keyword search
                            else:
                                subr_lst = []
                                word = re.match(r'get:subr:(.+?)(:.+)?$', data).group(1)
                                community = self.subr_db.get_community(word)

                                # set for not repeating subreddit in search results
                                subr_id_set = set([])

                                # if search is a subreddit name
                                if community:
                                    subr_lst.append(community)
                                    subr_id_set.add(community['_id'])

                                # match keyword
                                words = list(self.keyword_db.get_all_keywords())
                                words = keywords.match_keywords(words, word)

                                # sort keywords and get subreddits by keywords
                                words.sort(key=lambda x: x[0], reverse=True)
                                for w in words:
                                    if w[2] not in subr_id_set:
                                        subr_lst.append(self.subr_db.get_community_by_id(w[2]))
                                        subr_id_set.add(w[2])

                                sockobj.send(pickle.dumps(subr_lst))

                        elif re.match(r'new:user:(.+):(.+)', data):
                            # add user to db
                            m_obj = re.match(r'new:user:(.+):(.+)', data)
                            new_user = db.user(m_obj.group(1), m_obj.group(2))

                            if not new_user.name_exists():
                                new_user.add_to_db()
                                sockobj.send(f'signup good:{m_obj.group(1)}:False'.encode())
                                # add user to user_ip dict
                                user_ip[m_obj.group(1)] = sockobj
                            else:
                                sockobj.send('username already in use'.encode())

                        elif re.match(r'exist:user:(.+):(.+)', data):
                            # client login
                            m_obj = re.match(r'exist:user:(.+):(.+)', data)
                            exist_user = db.user(m_obj.group(1), m_obj.group(2))

                            if exist_user.user_exists():
                                if not m_obj.group(1) in self.user_ban_db.get_all_user():
                                    sockobj.send(f'login good:{m_obj.group(1)}:{str(exist_user.is_admin())}'.encode())
                                    if not exist_user.is_admin():
                                        # add user to user_ip dict
                                        user_ip[m_obj.group(1)] = sockobj
                                else:
                                    # in case user is banned
                                    sockobj.send(f'banned_user'.encode())
                            else:
                                sockobj.send('invalid password or username'.encode())

                        elif re.match(r'new:subr:(.+):(.+)', data):
                            # new subreddit creation
                            id_lst = [1]
                            id_lst.extend(self.subr_db.get_all_id())

                            m_obj = re.match(r'new:subr:(.+):(.+)', data)

                            if not self.subr_db.community_exists(m_obj.group(1)):
                                create_subr = True

                                all_subr = self.subr_db.get_all_communities()
                                subr_names = []
                                for subr in all_subr: subr_names.append(subr['name']) 

                                all_keywords = list(self.keyword_db.get_all_keywords())

                                # check similarity between new subreddit and existing subreddit, send alert if it is over 0.85
                                for name in subr_names:
                                    if keywords.get_similarity(name, m_obj.group(1)) >= 0.85:
                                        create_subr = False
                                        sockobj.send(f'sure about subr:{name}'.encode())

                                # send alert if new subreddit is an existing keyword
                                if create_subr:
                                    for w in all_keywords:
                                        if w['word'] == keywords.stem_keyword(m_obj.group(1)):
                                            create_subr = False
                                            sockobj.send(f'sure about subr:{self.subr_db.get_community_by_id(w["subr_id"])["name"]}'.encode())

                                if create_subr: 
                                    # create new subreddit                                   
                                    self.subr_db.new_community(m_obj.group(1), m_obj.group(2), max(id_lst) + 1)
                                    sockobj.send('subr_created'.encode())

                            else:
                                sockobj.send('community name already in use'.encode())

                        elif re.match(r'after_alert:new:subr:(.+):(.+)', data):
                            # create subreddit after alert
                            id_lst = [1]
                            id_lst.extend(self.subr_db.get_all_id())

                            m_obj = re.match(r'after_alert:new:subr:(.+):(.+)', data)
                            self.subr_db.new_community(m_obj.group(1), m_obj.group(2), max(id_lst) + 1)

                        elif re.match(r'(\d+)new:post:(.+):(.+):(.+):(.+):(.+)', data):
                            # new post creation

                            m_obj = re.match(r'(\d+)new:post:(.+):(.+):(.+):(.+):(.+)', data)
                            full_data = data
                            byte_num = int(m_obj.group(1))

                            # recieve over buffer
                            if byte_num > 4096:
                                while len(full_data) < byte_num:
                                    recv = sockobj.recv(BUFF).decode()
                                    full_data += recv

                            m_obj = re.match(r'(\d+)new:post:(.+):(.+):(.+):(.+):(.+)', full_data)
                            # add new post to database

                            if self.subr_db.community_exists(m_obj.group(4)):
                                
                                # if profanity is not allowed and it is detectected, send alert 
                                if ((bp.profanity.contains_profanity(m_obj.group(5)) or (m_obj.group(2) == 'false' and bp.profanity.contains_profanity(m_obj.group(6)))) 
                                    and self.settings['profanity_approach'] == 'block'):

                                    sockobj.send('profanity_detected'.encode())
                                else:
                                    id_lst = [1]
                                    id_lst.extend(self.post_db.get_all_id())

                                    if m_obj.group(2) == 'true':
                                        is_img = True
                                    else:
                                        is_img = False

                                    images_path = str(reddit.__file__).replace(r'reddit\__init__.py', r'images')    # images path
                                    new_id = max(id_lst) + 1    # post id

                                    # censor profanity in new text post
                                    if self.settings['profanity_approach'] == 'censor' and not is_img:
                                        self.post_db.new_post(is_img, m_obj.group(3), self.subr_db.get_subr_id(m_obj.group(4)), bp.profanity.censor(m_obj.group(5)), bp.profanity.censor(m_obj.group(6)), new_id)

                                    # censor profanity in new image post
                                    elif self.settings['profanity_approach'] == 'censor':
                                        img = base64.b64decode(m_obj.group(6))
                                        with open(f'{images_path}\img{new_id}.jpg', 'wb') as obj:
                                            obj.write(img)
                                        self.post_db.new_post(is_img, m_obj.group(3), self.subr_db.get_subr_id(m_obj.group(4)), bp.profanity.censor(m_obj.group(5)), f'{images_path}\img{new_id}.jpg', new_id)

                                    # add image post
                                    elif is_img:
                                        img = base64.b64decode(m_obj.group(6))
                                        with open(f'{images_path}\img{new_id}.jpg', 'wb') as obj:
                                            obj.write(img)
                                        self.post_db.new_post(is_img, m_obj.group(3), self.subr_db.get_subr_id(m_obj.group(4)), m_obj.group(5), f'{images_path}\img{new_id}.jpg', new_id)
                                    
                                    # add text post
                                    else:
                                        self.post_db.new_post(is_img, m_obj.group(3), self.subr_db.get_subr_id(m_obj.group(4)), m_obj.group(5), m_obj.group(6), new_id)

                                    self.subr_db.update_time(m_obj.group(4))

                                    # get text of all subreddit
                                    text = ''
                                    for post in self.post_db.get_posts_by_subr_id(self.subr_db.get_subr_id(m_obj.group(4))):
                                        text += post['title'] + '.\n'
                                        if not post['is_img']:
                                            text += post['content'] + '\n\n'
                                        for comment in self.comment_db.get_comments_by_post_id(post['_id']):
                                            text += comment['text'] + '\n\n'
                                    
                                    # extract keywords and add to db
                                    self.keyword_db.new_keywords(keywords.get_keywords_with_scores(text, self.settings['max_ngram_size'], self.settings['duplication_threshold']),  self.subr_db.get_subr_id(m_obj.group(4)))
                                    sockobj.send('post_created'.encode())
                            else:
                                sockobj.send('no such subreddit'.encode())

                        elif re.match(r'new:comment:(.+):(.+):(.+)', data):
                            # new comment

                            m_obj = re.match(r'new:comment:(.+):(.+):(.+)', data)
                            # if profanity is not allowed and it is detectected, send alert 
                            if bp.profanity.contains_profanity(m_obj.group(3)) and self.settings['profanity_approach'] == 'block':
                                sockobj.send('profanity_detected'.encode())
                            else:
                                id_lst = [1]
                                id_lst.extend(self.comment_db.get_all_id())
                                
                                # censor profanity in new comment
                                if self.settings['profanity_approach'] == 'censor':
                                    self.comment_db.new_comment(max(id_lst) + 1, m_obj.group(1), m_obj.group(2), bp.profanity.censor(m_obj.group(3)))

                                # add new comment. dont censor
                                else:
                                    self.comment_db.new_comment(max(id_lst) + 1, m_obj.group(1), m_obj.group(2), m_obj.group(3))
                                self.subr_db.update_time(self.post_db.get_subr_id_by_id(m_obj.group(1)))

                                # get text of all subreddit
                                text = ''
                                for post in self.post_db.get_posts_by_subr_id(self.post_db.get_post_by_id(m_obj.group(1))['subr_id']):
                                    text += post['title'] + '.\n'
                                    if not post['is_img']:
                                        text += post['content'] + '\n\n'
                                    for comment in self.comment_db.get_comments_by_post_id(post['_id']):
                                        text += comment['text'] + '\n\n'

                                # extract keywords and add to db
                                self.keyword_db.new_keywords(keywords.get_keywords_with_scores(text, self.settings['max_ngram_size'], self.settings['duplication_threshold']),  self.post_db.get_post_by_id(int(m_obj.group(1)))['subr_id'])
                                self.send_post(sockobj, m_obj.group(1))

                        elif re.match(r'get:comments:(.+)', data):
                            # client requesting post
                            post_id = re.match(r'get:comments:(.+)', data).group(1)
                            self.send_post(sockobj, post_id)

                        elif data == 'get:admin:subrs:users':
                            # send subreddits with number of users in them
                            st = 'admin:subrs:users'
                            for com in self.subr_db.get_all_communities():
                                subr_name = com['name']
                                user_num = str(len(self.users_in_subr[subr_name]))
                                st += f';{subr_name}:{user_num}'

                            sockobj.send(st.encode())

                        elif data == 'get:admin:subrs:date':
                            # send subreddits with their creation date
                            st = 'admin:subrs:date'
                            for com in self.subr_db.get_all_communities():
                                subr_name = com['name']
                                subr_date = com['date']
                                st += f';{subr_name}:{subr_date}'
                                
                            sockobj.send(st.encode())

                        elif re.match(r'get:admin:subrs:keyword:(.+)', data):
                            # send subreddits by a keyword. send with score
                            keyword = re.match(r'get:admin:subrs:keyword:(.+)', data).group(1)
                            all_keywords = self.keyword_db.get_all_keywords()
                            st = 'admin:subrs:keyword'
                            for w in all_keywords:
                                if keyword == w['word']:
                                    subr_name = self.subr_db.get_community_by_id(w['subr_id'])['name']
                                    score = w['score']
                                    st += f';{subr_name}:{str(score)}'

                            sockobj.send(st.encode())

                        elif re.match(r'get:admin:subr_info:(.+)', data):
                            # send subreddit page for admin
                            community_name = re.match(r'get:admin:subr_info:(.+)', data).group(1)
                            community = self.subr_db.get_community(community_name)
                            
                            # subreddit information
                            st = f'admin:subr_page:{community["name"]}:{community["description"]}:{community["_id"]}:{community["date"]};'

                            # current users in subreddit
                            user_time_lst = []
                            for user in self.users_in_subr[community_name]:
                                user_time_lst.append((user, time.time() - user_time_in_subr[user]))

                            st += str(user_time_lst)

                            posts = self.post_db.get_posts_by_subr_id(self.subr_db.get_subr_id(community["name"]))
                            for p in posts:
                                # text post
                                if not p["is_img"]:
                                        st += f';{p["_id"]}:{p["is_img"]}:{p["user"]}:{p["title"]}:{p["content"]}:{p["date"]}'

                                # image post
                                else:
                                    with open(p["content"], 'rb') as obj:
                                        img = base64.b64encode(obj.read())
                                    st += f';{p["_id"]}:{p["is_img"]}:{p["user"]}:{p["title"]}:{img.decode()}:{p["date"]}'

                            # add data length
                            st = str(len(st + str(len(st)))) + st

                            sockobj.send(st.encode())

                        elif re.match(r'in_home_page:(.+)', data):
                            # remove user from data self.users_in_subr. sent when client exits subreddit
                            user = re.match(r'in_home_page:(.+)', data).group(1)
                            for subr in self.users_in_subr:
                                if user in self.users_in_subr[subr]:
                                    self.users_in_subr[subr].remove(user)

                        elif re.match(r'ip_ban:(.+)', data):
                            user = re.match(r'ip_ban:(.+)', data).group(1)
                            if user in user_ip:
                                # add banned ip to db
                                self.ip_ban_db.add_ip(user_ip[user].getpeername()[0])

                                # stop communication with banned ip send message
                                for sock in writeables:
                                    if sock.getpeername()[0] == user_ip[user].getpeername()[0]:
                                        sock.send('banned'.encode())

                                        readsocks.remove(sock)
                                        writesocks.remove(sock)

                                        # delete banned ip from user_ip dict
                                        user_ip = {key:val for key, val in dict(user_ip).items() if val.getpeername()[0] != sock.getpeername()[0]}
                                        
                                        # remove banned not logged in users from self.users_in_subr dict
                                        self.remove_user_in_subr(sock.getpeername()[0])

                                        sock.close()

                                # get not banned users
                                current_users = []
                                for key, val in dict(user_ip).items():
                                    current_users.append(key)
                                    
                                # remove banned logged in users from self.users_in_subr dict
                                for key1, val1 in dict(self.users_in_subr).items():
                                    for u in val1:
                                        if u not in current_users:
                                            self.users_in_subr[key1].remove(u)

                            else:
                                self.ip_ban_db.add_ip(user)
                                for sock in writeables:
                                    if sock.getpeername()[0] == user:
                                        sock.send('banned'.encode())

                                        # remove banned ip from ip from users_in_subr dicr
                                        for subr in self.users_in_subr:
                                            if sock.getpeername()[0] in self.users_in_subr[subr]:
                                                self.users_in_subr[subr].remove(sock.getpeername()[0])
                                        
                                        readsocks.remove(sock)
                                        writesocks.remove(sock)
                                        sock.close()

                        elif re.match(r'ban_user:(.+)', data):
                            user = re.match(r'ban_user:(.+)', data).group(1)
                            self.user_ban_db.add_user(user)
                            user_ip[user].send('banned'.encode())

                            # stop communication with banned user
                            readsocks.remove(user_ip[user])
                            writesocks.remove(user_ip[user])
                            user_ip[user].close()

                            del user_ip[user]
                            self.remove_user_in_subr(user)

                        elif re.match(r'warning:(.+):(.+)', data):
                            m_obj = re.match(r'warning:(.+):(.+)', data)
                            user = m_obj.group(1)
                            
                            msg = m_obj.group(2)
                            # send warning from admin to user
                            if user in user_ip:
                                sock = user_ip[user]
                                sock.send(f'warning:{msg}'.encode())
                            else:
                                ip = user
                                # send warning from admin to user that is not logged in
                                for sock in writeables:
                                    if sock.getpeername()[0] == ip:
                                        sock.send(f'warning:{msg}'.encode())

                        elif re.match(r'new:keyword:(.+):(.+):(.+)', data):
                            # add new keyword (from admin)
                            m_obj = re.match(r'new:keyword:(.+):(.+):(.+)', data) 
                            keyword = m_obj.group(1)
                            score = m_obj.group(2)
                            subr_name = m_obj.group(3)

                            self.keyword_db.new_keyword(keyword, float(score), self.subr_db.get_subr_id(subr_name))

                        elif re.match(r'delete:keyword:(.+):(.+)', data):
                            # delete keyword (admin)
                            m_obj = re.match(r'delete:keyword:(.+):(.+)', data) 
                            keyword = m_obj.group(1)
                            subr_name = m_obj.group(2)

                            self.keyword_db.delete_by_subr_id_and_word(keyword, self.subr_db.get_subr_id(subr_name))

                        elif re.match(r'admin:get:subr:keyword(.+)', data):
                            # send keywords of a subreddit
                            subr_name = re.match(r'admin:get:subr:keyword:(.+)', data).group(1)
                            words = self.keyword_db.get_keywords_by_subr(self.subr_db.get_subr_id(subr_name))
                            st = 'admin:subr:keywords'
                            for w in words:
                                    keyword = w['word']
                                    score = w['score']
                                    st += f';{keyword}:{str(score)}'

                            sockobj.send(st.encode())

                        elif re.match(r'admin:get:subr:users:(.+)', data):
                            try:
                                subr_name = re.match(r'admin:get:subr:users:(.+)', data).group(1)
                                
                                # sebd users in a subreddit
                                user_time_lst = []
                                for user in self.users_in_subr[community_name]:
                                    user_time_lst.append((user, time.time() - user_time_in_subr[user]))

                                sockobj.send(f'subr:users:{str(user_time_lst)}'.encode())
                            except AttributeError:
                                pass

                        elif 'get:active_users' == data:
                            # send all users in different subreddits with duration
                            st = 'admin:active_users'
                            for subr, users in self.users_in_subr.items():
                                for u in users:
                                    st += f';{u}:{subr}:{str(int(time.time() - (user_time_in_subr[u])))}'

                            sockobj.send(st.encode())

                        elif re.match(r'change:subr_date:(.+):(.+)', data):
                            # change subreddit date
                            m_obj = re.match(r'change:subr_date:(.+):(.+)', data)
                            subr = m_obj.group(1)
                            new_date = m_obj.group(2)

                            old_date = self.subr_db.get_community(subr)['date']

                            new_date_split = new_date.split('-')
                            old_date_split = old_date.split('-')

                            # create date objects from new date and old date
                            d1 = date(int(new_date_split[2]), int(new_date_split[1]), int(new_date_split[0]))
                            d2 = date(int(old_date_split[2]), int(old_date_split[1]), int(old_date_split[0]))

                            if d1 <= date.today():
                                days_dif = abs(d1 - d2).days
                                
                                # check if date difference is positive or negative
                                if d2 > d1:
                                    increase_date = False
                                else:
                                    increase_date = True

                                # change dates of posts and comments in subreddit
                                subr_id = self.subr_db.get_subr_id(subr)
                                self.post_db.update_dates_by_subr_id(days_dif, subr_id, increase_date)
                                for post in self.post_db.get_posts_by_subr_id(subr_id):
                                    self.comment_db.update_dates_by_post_id(days_dif, str(post['_id']), increase_date)
                                
                                # change subreddit date
                                self.subr_db.update_date(subr_id, new_date)
                        
                        elif data == 'get:current_settings':
                            # send current settings
                            sockobj.send(f'current_settings:{self.settings["max_ngram_size"]}:{self.settings["duplication_threshold"]}:{self.settings["profanity_approach"]}'.encode())

                        elif re.match(r'setting:(.+):(.+)', data):
                            # change a setting
                            split_data = data.split(':')
                            field = split_data[1]
                            value = split_data[2]

                            if field == 'max_ngram_size':
                                self.settings_db.change_setting(field, int(value))
                                self.settings[field] = int(value)

                            if field == 'duplication_threshold':
                                self.settings_db.change_setting(field, float(value))
                                self.settings[field] = float(value)

                            if field == 'profanity_approach':
                                self.settings_db.change_setting(field, value)
                                self.settings[field] = value

                # in case client disconnects
                except ConnectionResetError or ConnectionAbortedError:
                    readsocks.remove(sockobj)
                    writesocks.remove(sockobj)

                    try:
                        # remove user from self.users_in_subr dict
                        if list(user_ip.keys())[list(user_ip.values()).index(sockobj)]:
                            self.remove_user_in_subr(list(user_ip.keys())[list(user_ip.values()).index(sockobj)])
                    except ValueError:
                        # remove ip from self.users_in_subr dict
                        self.remove_user_in_subr(sockobj.getpeername()[0])

                    # remove user that disconnected from user_ip dict
                    user_ip = {key:val for key, val in dict(user_ip).items() if val.getpeername() != sockobj.getpeername()}

                    print(f'disconnected: {str(sockobj.getpeername())} {str(id(sockobj))}')
                    sockobj.close()

if __name__ == '__main__':
    serv = server()
    serv.run_server()
