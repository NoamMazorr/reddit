from pymongo import MongoClient
import time, re, datetime
from datetime import date


class db:
    def __init__(self):
        '''
        cloud database: 'mongodb+srv://mazor:360putin@redditdb.bbh41.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'\n
        local database: 'localhost:27017'
        '''
        self.cluster = MongoClient('localhost:27017')
        self._db = self.cluster['redditDB']


class user(db):
    def __init__(self, name, password):
        super().__init__()
        self.name = name
        self.password = password

        self.users = self._db['Users']

    def name_exists(self):
        '''
        check if username already exists in db
        '''
        if self.users.find_one({'username': self.name}):
            return True
        return False

    def user_exists(self):
        '''
        check if user exists
        '''
        if self.users.find_one({'username': self.name, 'password': self.password}):
            return True
        return False

    def add_to_db(self):
        '''
        add user to db
        '''
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        self.users.insert_one({'username': self.name, 'password': self.password, 'admin': False, 'date': date_pattern.sub(r'\3-\2-\1', str(date.today()))})

    def is_admin(self):
        '''
        return True if user is admin False if not
        '''
        return self.users.find_one({'username': self.name, 'password': self.password})['admin']


class subr(db):
    def __init__(self):
        super().__init__()
        self.communities = self._db['communities']

    def new_community(self, name, description, id):
        '''
        add new community to db
        '''
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        self.communities.insert_one({'_id': id, 'name': name, 'description': description, 'last_active_time': time.time(), 'date': date_pattern.sub(r'\3-\2-\1', str(date.today()))})
        
    def get_community_by_id(self, id):
        '''
        get a community by id
        '''
        return self.communities.find_one({'_id': id})
    
    def get_community(self, name):
        '''
        get a community by its name
        '''
        return self.communities.find_one({'name': name})
        
    def community_exists(self, name):
        '''
        check if a community exists by name
        '''
        if self.communities.find_one({'name': name}):
            return True
        return False

    def get_all_communities(self):
        '''
        get all communities
        '''
        return self.communities.find({})

    def get_all_id(self):
        '''
        get existing ids in communities collection
        '''
        id_lst = []
        results = self.communities.find({}, {'_id': 1})
        for r in results:
            id_lst.append(r['_id'])
        
        return id_lst

    def update_time(self, subr_name): 
        '''
        update last activity time in subreddit to current time
        '''
        self.communities.update_one({'name': subr_name}, {"$set": {'last_active_time': time.time()}})

    def update_date(self, id, new_date):
        '''
        update subreddit time and update last activity time by difference between new date and previous date
        '''
        com = self.get_community_by_id(id)
        new_time = time.mktime(datetime.datetime.strptime(new_date, "%d-%m-%Y").timetuple())
        old_time = time.mktime(datetime.datetime.strptime(com['date'], "%d-%m-%Y").timetuple())

        self.communities.update_one({'_id': id}, {"$set": {'last_active_time': com['last_active_time'] + (new_time - old_time)}})
        self.communities.update_one({'_id': id}, {"$set": {'date': str(new_date)}})

    def delete_community(self, name):
        '''
        delete community by name
        '''
        self.communities.delete_one({'name': name})

    def get_subr_id(self, name):
        '''
        get community id by name 
        '''
        return self.communities.find_one({'name': name})['_id']


class post(db):
    def __init__(self):
        super().__init__()
        self.posts = self._db['posts']

    def new_post(self, is_img, user, subr_id, title, content, id):
        '''
        add new post to db
        '''
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        self.posts.insert_one({'_id': id, 'is_img': is_img, 'user': user, 'subr_id': subr_id, 'title': title, 'content': content, 'date': date_pattern.sub(r'\3-\2-\1', str(date.today())), 'post_time': time.time()})
        
    def get_all_id(self):
        '''
        get existing ids in posts collection
        '''
        id_lst = []
        results = self.posts.find({}, {'_id': 1})
        for r in results:
            id_lst.append(r['_id'])
        
        return id_lst
    
    def get_all_posts(self):
        '''
        get all posts
        '''
        return self.posts.find({})

    def get_posts_by_subr_id(self, subr_id):
        '''
        get posts by subreddit id
        '''
        return self.posts.find({'subr_id': subr_id})

    def get_post_by_cont(self, cont):
        '''
        get post by its content
        '''
        return self.posts.find({'content': cont})

    def get_post_by_id(self, post_id):
        '''
        get post by id
        '''
        return self.posts.find_one({'_id': int(post_id)})

    def get_subr_id_by_id(self, post_id):
        '''
        get subreddit id by post id
        '''
        return self.posts.find_one({'_id': int(post_id)})['subr_id']

    def delete_posts_by_subr_id(self, subr_id):
        '''
        delete posts by subreddit id
        '''
        self.posts.delete_many({'subr_id': subr_id})

    def update_dates_by_subr_id(self, days_dif, subr_id, increase_date):
        '''
        increase or decrease creation date of posts of a subreddit by days_dif
        '''
        posts = self.get_posts_by_subr_id(subr_id)
        for post in posts:
            post_date = datetime.datetime.strptime(post['date'], "%d-%m-%Y")
    
            if increase_date:
                # increased date
                new_date = post_date + datetime.timedelta(days=days_dif)
            else:
                # decreased date
                new_date = post_date - datetime.timedelta(days=days_dif)

            if date.today() < new_date.date():
                # dont increase date over the date today
                self.posts.update_one({'_id': post['_id']}, {"$set": {'date': date.today().strftime("%d-%m-%Y")}})
            else:
                # update date
                self.posts.update_one({'_id': post['_id']}, {"$set": {'date': new_date.strftime("%d-%m-%Y")}})


class comment(db):
    def __init__(self):
        super().__init__()
        self.comments = self._db['comments']

    def new_comment(self, id, post_id, user, text):
        '''
        add new comment to db
        '''
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        self.comments.insert_one({'_id': id, 'post_id': post_id, 'user': user, 'text': text, 'date': date_pattern.sub(r'\3-\2-\1', str(date.today()))})

    def get_comments_by_post_id(self, post_id):
        '''
        get comments by post id
        '''
        return self.comments.find({'post_id': str(post_id)})

    def delete_comments_by_post_id(self, post_id):
        '''
        delete comments by post id
        '''
        self.comments.delete_many({'post_id': str(post_id)})

    def get_all_id(self):
        '''
        get existing ids in comments collection
        '''
        id_lst = []
        results = self.comments.find({}, {'_id': 1})
        for r in results:
            id_lst.append(r['_id'])
        
        return id_lst

    def update_dates_by_post_id(self, days_dif, post_id, increase_date):
        '''
        increase or decrease creation date of comments of a post by days_dif
        '''
        comments = self.get_comments_by_post_id(post_id)
        for comment in comments:
            comment_date = datetime.datetime.strptime(comment['date'], "%d-%m-%Y")
    
            if increase_date:
                # increased date
                new_date = comment_date + datetime.timedelta(days=days_dif)
            else:
                # decreased date
                new_date = comment_date - datetime.timedelta(days=days_dif)
    
            if date.today() < new_date.date():
                # dont increase date over the date today
                self.comments.update_one({'_id': comment['_id']}, {"$set": {'date': date.today().strftime("%d-%m-%Y")}})
            else:
                # update date
                self.comments.update_one({'_id': comment['_id']}, {"$set": {'date': new_date.strftime("%d-%m-%Y")}})

class keyword_db(db):
    def __init__(self):
        super().__init__()
        self.keywords = self._db['keywords']

    def get_keywords_by_subr(self, subr_id):
        '''
        get keywords by subreddit id
        '''
        return self.keywords.find({'subr_id': subr_id})

    def delete_by_subr_id_and_word(self, word, subr_id):
        '''
        delete keywords by subreddit id and word
        '''
        self.keywords.delete_one({'word': word, 'subr_id': subr_id})

    def delete_by_id(self, id):
        '''
        delete keywords by subreddit id
        '''
        self.keywords.delete_one({'_id': id})

    def new_keywords(self, words, subr_id):
        '''
        add new keywords to a subreddit
        '''
        for word, score in words:
            subr_words = self.get_keywords_by_subr(subr_id)
            for old_word in subr_words:
                # delete old word that are the same as new words
                if old_word['word'] == word:
                    self.delete_by_id(old_word['_id']) 
            self.keywords.insert_one({'score': 1.0 / score, 'word': word, 'subr_id': subr_id})

    def new_keyword(self, word, score, subr_id):
        '''
        add new keyword to a subreddit
        '''
        subr_words = self.get_keywords_by_subr(subr_id)
        for old_word in subr_words:
            if old_word['word'] == word:
                # delete old word that is the same as new word
                self.delete_by_id(old_word['_id'])

        self.keywords.insert_one({'score': score, 'word': word, 'subr_id': subr_id})

    def get_keywords_by_word(self, word):
        '''
        get keywords by a word
        '''
        return self.keywords.find({'word': word})

    def get_all_keywords(self):
        '''
        get all keywords
        '''
        return self.keywords.find({})

    def delete_many_by_subr_id(self, subr_id):
        '''
        delete keywords by subreddit id
        '''
        self.keywords.delete_many({'subr_id': subr_id})

class ip_bans(db):
    def __init__(self):
        super().__init__()
        self.banned_ip = self._db['banned ip addresses']

    def add_ip(self, ip):
        '''
        add ip to banned ips collection
        '''
        return self.banned_ip.insert_one({'ip': ip})

    def get_all_ip(self):
        '''
        get all banned ips
        '''
        all_ip = []
        for ip in self.banned_ip.find({}):
            all_ip.append(ip['ip'])

        return all_ip

class user_bans(db):
    def __init__(self):
        super().__init__()
        self.banned_users = self._db['banned users']

    def add_user(self, user):
        '''
        add user to banned users collection
        '''
        return self.banned_users.insert_one({'user': user})

    def get_all_user(self):
        '''
        get all banned users
        '''
        all_users = []
        for user in self.banned_users.find({}):
            all_users.append(user['user'])

        return all_users


class settings(db):
    def __init__(self):
        super().__init__()
        self.settings = self._db['settings']

    def change_setting(self, field, value):
        '''
        change setting
        '''
        return self.settings.update_one({}, {"$set": {field: value}})

    def get_settings(self):
        '''
        get current settings
        '''
        return self.settings.find_one({})

    def set_settings(self):
        '''
        set settings when starting to work with a new database
        '''
        self.settings.insert_one({'duplication_threshold': 0.1, 'max_ngram_size': 3, 'profanity_approach': 'block'})
