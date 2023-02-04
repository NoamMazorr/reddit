from socket import *
from tkinter import *
from tkinter import filedialog as fd
from PIL import Image, ImageTk
from tkinter import ttk
import re, pickle, _thread, base64, datetime, time, sv_ttk, os


class tk_main:
    def __init__(self):
        pass


    def find_subreddit(self, e):
        '''
        request subreddit that matches input
        '''
        search_input = self.search_entry.get().strip()
        try:
            sock.send(f'get:subr:{search_input}:{self.username}'.encode())
        except AttributeError:
            sock.send(f'get:subr:{search_input}'.encode())


    def in_home_page(self):
        '''
        inform server that a user is not in a specific subreddit
        '''
        try:
            sock.send(f'in_home_page:{self.username}'.encode())
        except AttributeError:
            sock.send(f'in_home_page:{self.IP}'.encode())


    def get_subreddit_page(self, subr):
        '''
        get subreddit information
        '''
        try:
            sock.send(f'get:subr:{subr}:{self.username}'.encode())
        except AttributeError:
            sock.send(f'get:subr:{subr}'.encode())


    def start_req_thread(self, func):
        '''
        initiate admin refresh request thread
        '''
        self.req_func = func
        _thread.start_new_thread(self.req_thread, ())


    def req_subr_users(self):
        '''
        change request to users in a subreddit
        '''
        self.wait_time = 10
        self.last_update_time = time.time()
        self.req_func = self.get_subr_users
        self.get_subr_users()

    
    def req_subr_keywords(self):
        '''
        change request to keywords in a subreddit
        '''
        self.wait_time = 15
        self.last_update_time = time.time()
        self.req_func = self.get_subr_keywords
        self.get_subr_keywords()


    def req_subrs_users(self):
        '''
        change request to subreddits with number of users in them
        '''
        if self.last_update_time:
            self.wait_time = 10
            self.last_update_time = time.time()
            self.req_func = self.get_admin_subrs_users
            self.date_btn['state'] = NORMAL
            self.user_num_btn['state'] = DISABLED
            self.get_admin_subrs_users()


    def req_subrs_date(self):
        '''
        change request to subreddits with their creation date
        '''
        self.wait_time = 10
        self.last_update_time = time.time()
        self.req_func = self.get_admin_subrs_date
        self.get_admin_subrs_date()


    def req_subrs_keyword(self, *args):
        '''
        change request to subreddits that have a specific keyword
        '''
        self.wait_time = 10
        self.last_update_time = time.time()
        keyword = self.keyword_entry.get()
        self.req_func = lambda: self.refresh_admin_subrs_keyword(keyword)
        self.get_admin_subrs_keyword()


    def req_thread(self):
        '''
        send request for admin informaion after a set amout of time to refresh information
        '''
        self.last_update_time = time.time()
        self.wait_time = 10
        while True:
            # if wait_time has passed send request
            if time.time() - self.last_update_time >= self.wait_time:
                self.req_func()
                self.last_update_time = time.time()
            
            # if last_update_time has been set to over time.time() stop thread
            elif time.time() - self.last_update_time < 0:
                del self.last_update_time
                break


    def get_admin_subrs_users(self):
        '''
        get subreddits with number of users
        '''
        sock.send('get:admin:subrs:users'.encode())


    def get_admin_subrs_date(self):
        '''
        get subreddits with the date of their creation
        '''
        self.date_btn['state'] = DISABLED
        self.user_num_btn['state'] = NORMAL
        sock.send('get:admin:subrs:date'.encode())


    def get_admin_subrs_keyword(self):
        '''
        get subreddits by keyword
        '''
        self.date_btn['state'] = NORMAL
        self.user_num_btn['state'] = NORMAL
        sock.send(f'get:admin:subrs:keyword:{self.keyword_entry.get()}'.encode())
        self.keyword_entry.delete(0, 'end')


    def refresh_admin_subrs_keyword(self, keyword):
        '''
        update subreddits by keyword (refresh)
        '''
        sock.send(f'get:admin:subrs:keyword:{keyword}'.encode())


    def get_subr_keywords(self):
        '''
        get all keywords of a subreddit
        '''
        sock.send(f'admin:get:subr:keyword:{self.current_subr_name}'.encode())

    
    def get_subr_users(self):
        '''
        get all users in a subreddit
        '''
        sock.send(f'admin:get:subr:users:{self.current_subr_name}'.encode())
    

    def get_admin_community(self):
        '''
        get subreddit content for admin
        '''
        # make sure refresh thread does not communicate while getting subreddit information
        self.last_update_time = time.time() + 1000.0
        try:
            sock.send(f'get:admin:subr_info:{self.data_List.item(self.data_List.focus())["values"][0]}'.encode())
        except TclError:
            pass

    
    def get_all_active_users(self):
        '''
        get all users browsing subreddits
        '''
        sock.send('get:active_users'.encode())


    def get_current_settings(self):
        '''
        get current settings for admin too see
        '''
        sock.send('get:current_settings'.encode())


    def send_signup(self):
        '''
        send information of new user
        '''
        sock.send(f'new:user:{self.name_entry.get()}:{self.pass_entry.get()}'.encode())


    def send_login(self):
        '''
        send togin information
        '''
        sock.send(f'exist:user:{self.name_entry.get()}:{self.pass_entry.get()}'.encode())


    def send_new_community(self):
        '''
        send server new subreddit for creation
        '''
        sock.send(f'new:subr:{self.comm_name_entry.get()}:{self.description_entry.get()}'.encode())


    def send_warning(self):
        '''
        send warning of admin
        '''
        try:
            sock.send(f'warning:{self.data_List.item(self.data_List.focus())["values"][0]}:{self.warning_txt_entry.get()}'.encode())
            self.warning_txt_entry.delete(0, END)
        except TclError:
            pass


    def change_subr_date(self, subr):
        '''
        send new subreddit date
        '''
        if len(self.month_entry.get()) > 1:
            sock.send(f'change:subr_date:{subr}:{self.day_entry.get()}-0{self.month_entry.get()}-{self.year_entry.get()}'.encode())
        else:
            sock.send(f'change:subr_date:{subr}:{self.day_entry.get()}-{self.month_entry.get()}-{self.year_entry.get()}'.encode())
        self.date_page.destroy()
        self.wait_time = 10


    def del_keyword(self):
        '''
        send keyword for server to delete from db
        '''
        sock.send(f'delete:keyword:{self.data_List.item(self.data_List.focus())["values"][0]}:{self.current_subr_name}'.encode())


    def ip_ban(self):
        '''
        send new banned ip
        '''
        try:
            sock.send(f'ip_ban:{self.data_List.item(self.data_List.focus())["values"][0]}'.encode())
        except TclError:
            pass


    def ban_user(self):
        '''
        send new banned user
        '''
        try:
            sock.send(f'ban_user:{self.data_List.item(self.data_List.focus())["values"][0]}'.encode())
        except TclError:
            pass


    def send_new_keyword(self):
        '''
        send new keyword of a subreddit
        '''
        sock.send(f'new:keyword:{self.add_keyword_entry.get()}:{self.keyword_score.get()}:{self.current_subr_name}'.encode())
        self.add_keyword_page.destroy()
    

    def new_community_after_alert(self):
        '''
        create new community after an alert of a similar subreddit existing
        '''
        sock.send(f'after_alert:new:subr:{self.comm_name_entry.get()}:{self.description_entry.get()}'.encode())
        self.destroy_root2()
        self.send_btn['state'] = NORMAL


    def send_img_post(self):
        '''
        send new image post
        '''

        # send image as base64
        with open(f'{self.img_file}', 'rb') as obj:
            img = base64.b64encode(obj.read())
        
        send_bytes = f'new:post:true:{self.username}:{self.subr_entry.get()}:{self.title_entry.get()}:'.encode()
        send_bytes += img

        # add number of bytes sent
        byte_num = str(len(send_bytes) + len(str(len(send_bytes)))).encode()
        send_bytes = byte_num + send_bytes

        sock.send(send_bytes)


    def change_max_ngram_size(self):
        '''
        change setting max_ngram_size
        '''
        sock.send(f'setting:max_ngram_size:{self.ngram_size_entry.get()}'.encode())


    def change_duplication_threshold(self):
        '''
        change setting duplication_threshold
        '''
        sock.send(f'setting:duplication_threshold:{self.duplication_threshold_entry.get()}'.encode())


    def change_profanity_approach(self):
        '''
        change setting profanity_approach
        '''
        sock.send(f'setting:profanity_approach:{self.profanity_option.get()}'.encode())


    def send_txt_post(self):
        '''
        send new text post
        '''

        # replace \n so text can be saved in db
        text = self.txt_entry.get("1.0","end").strip().replace("\n", "\\n")
        st = f'new:post:false:{self.username}:{self.subr_entry.get()}:{self.title_entry.get()}:{text}'
        # add number of bytes
        st = str(len(st) + len(str(len(st)))) + st

        sock.send(st.encode())


    def new_comment(self, post_id):
        '''
        send new comment of client
        '''
        text = self.comment_entry.get("1.0", "end").strip().replace("\n", "\\n")
        self.comment_entry.delete('1.0', END)
        sock.send(f'new:comment:{post_id}:{self.username}:{text}'.encode())

    
    def get_comments_by_id(self, post):
        '''
        send post id to get comments
        '''
        post = eval(post)
        sock.send(f'get:comments:{str(post["_id"])}'.encode())

        
    def frame_width(self, e):
        '''
        keep canvas frame the width of root
        '''
        try:
            canvas_width = root.winfo_width()
            self.my_canvas.itemconfig(self.canvas_window, width = canvas_width)
        except TclError: 
            pass


    def banned(self):
        '''
        alert for banned user
        '''
        self.main_frame.destroy()
        try:
            self.my_menu.destroy()
        except:
            pass
        root.geometry('400x250+400+200')
        root.minsize(150, 150)
        root.update()
        Label(root, text='unfortunately you are banned', bg='white', font='roboto 18 ').pack(pady=(75,0))


    def show_subr_keywords(self, keywords):
        '''
        sort and insert keywords of a subreddit
        '''
        self.clear_all()
        keywords.sort(key=lambda x: x[1], reverse=True)

        for item in keywords:
            self.data_List.insert(parent='', index=END, text='', values=item)


    def show_subr_users(self, users):
        '''
        insert users in a subreddit
        '''
        self.clear_all()
        for user in users:
            self.data_List.insert(parent='', index=END, text='', values=user)


    def show_active_users(self, users):
        '''
        insert all users in different sureddits and their time in them
        '''
        self.data_List.delete(0, 'end')
        users = users.split(';')
        for user in users:
            user = user.split(':')
            duration = str(datetime.timedelta(seconds=int(user[2])))
            self.data_List.insert(END, f'{user[0]} is in {user[1]} for {duration}')


    def clear_all(self):
        '''
        delete items from treeview
        '''
        for item in self.data_List.get_children():
            self.data_List.delete(item)


    def sort_by_keyword(self, subrs_info):
        '''
        sort and insert subreddit by keyword input
        '''
        self.data_List.heading("two", text="score")
        self.clear_all()
        subrs_info.sort(key=lambda x: x[1], reverse=True)
        for subr in subrs_info:
            self.data_List.insert(parent='', index=END, text='', values=subr)


    def sort_by_date(self, subrs_info):
        '''
        sort and insert subreddits by their creation dates
        '''
        self.data_List.heading("two", text="date")
        self.clear_all()
        subrs_info.sort(key=lambda x: datetime.datetime.strptime(x[1], '%d-%m-%Y'), reverse=True)
        for subr in subrs_info:
            self.data_List.insert(parent='', index=END, text='', values=subr)


    def sort_by_user_amount(self, subrs_info):
        '''
        sort and insert subreddits by the number of users in them
        '''
        self.data_List.heading("two", text="number of users")
        self.clear_all()
        subrs_info.sort(reverse=True)
        for subr in subrs_info:
            self.data_List.insert(parent='', index=END, text='', values=subr)


    def destroy_admin_info(self):
        '''
        destroy previous page. add canvas with scrollbar for admin subreddit page
        '''
        self.info_frame.destroy()

        self.info_frame = Frame(self.main_frame, background='white')
        self.info_frame.pack(fill=BOTH, expand=YES)

        self.my_canvas = Canvas(self.info_frame, bg='white', relief=FLAT, highlightthickness=0)
        self.my_canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        self.canvas_frame = Frame(self.my_canvas, bg='white', width=self.my_canvas.winfo_width())
        self.canvas_window = self.my_canvas.create_window((0, 0), window=self.canvas_frame, anchor=NW)

        yscrollbar = ttk.Scrollbar(self.info_frame, orient='vertical', command=self.my_canvas.yview)
        yscrollbar.pack(side=RIGHT, fill=Y)

        self.my_canvas.configure(yscrollcommand=yscrollbar.set)

        self.my_canvas.bind('<Configure>', lambda e: self.my_canvas.configure(scrollregion=self.my_canvas.bbox('all')))

        canvas_width = root.winfo_width() 
        self.my_canvas.itemconfig(self.canvas_window, width = canvas_width)

        self.main_frame.bind('<Configure>', self.frame_width)


    def on_close_date_page(self):
        self.wait_time = 10
        self.date_page.destroy()


    def change_date_page(self):
        '''
        popup for changing date of subreddit
        '''
        self.wait_time = 600
        selcted_subr = self.data_List.item(self.data_List.focus())["values"][0]

        self.date_page = Tk()
        self.date_page.geometry('400x250+400+200')
        self.date_page.minsize(150, 150)
        self.date_page.config(bg='white')

        # add sv_ttk theme to popup
        sv_ttk_path = str(sv_ttk.__file__).replace(r'\__init__.py', '')
        self.date_page.call("source", fr"{sv_ttk_path}\sun-valley.tcl")
        self.date_page.call("set_theme", "light")

        self.date_page.protocol("WM_DELETE_WINDOW", self.on_close_date_page)

        self.date_frame = Frame(self.date_page, bg = 'white')
        self.date_frame.pack(pady=(50, 0 ))

        Label(self.date_frame, text='day: ', bg='white').pack(side=LEFT)

        self.day_entry = ttk.Entry(self.date_frame,  width=3)
        self.day_entry.pack(side=LEFT, padx=(0, 20))

        Label(self.date_frame, text='month: ', bg='white').pack(side=LEFT)

        self.month_entry = ttk.Entry(self.date_frame,  width=3)
        self.month_entry.pack(side=LEFT, padx=(0, 20))

        Label(self.date_frame, text='year: ', bg='white').pack(side=LEFT)

        self.year_entry = ttk.Entry(self.date_frame,  width=5)
        self.year_entry.pack(side=LEFT)

        send_btn = ttk.Button(self.date_page, width=12, text='change date', command=lambda: self.change_subr_date(selcted_subr))
        send_btn.pack(pady=(50, 0))

        self.date_page.mainloop()


    def show_warning(self, msg):
        '''
        show warning from admin to user
        '''
        self.warning_page = Tk()
        self.warning_page.geometry('500x250+400+200')
        self.warning_page.minsize(150, 150)
        self.warning_page.configure(background='white')

        Label(self.warning_page, text=msg, font='roboto 12', bg='white').pack(pady=75)

        self.warning_page.mainloop()


    def add_keyword(self):
        '''
        add keyword to subreddit popup
        '''
        self.add_keyword_page = Tk()
        self.add_keyword_page.geometry('400x350+400+200')
        self.add_keyword_page.minsize(150, 150)
        self.add_keyword_page.configure(background='white')

        # add sv_ttk theme to popup
        sv_ttk_path = str(sv_ttk.__file__).replace(r'\__init__.py', '')
        self.add_keyword_page.call("source", fr"{sv_ttk_path}\sun-valley.tcl")
        self.add_keyword_page.call("set_theme", "light")

        Label(self.add_keyword_page, text='keyword:', font='roboto 12', bg='white').pack(pady=(75,5))

        self.add_keyword_entry = ttk.Entry(self.add_keyword_page,  width=25)
        self.add_keyword_entry.pack()

        Label(self.add_keyword_page, text='score:', font='roboto 12', bg='white').pack(pady=(25,5))

        self.keyword_score = ttk.Entry(self.add_keyword_page,  width=25)
        self.keyword_score.pack()

        send_btn = ttk.Button(self.add_keyword_page, width=14, text='add keyword', command=self.send_new_keyword)
        send_btn.pack(pady=(30, 0))

        self.add_keyword_page.mainloop()
        

    def switch_to_subr_keywords(self):
        '''
        switch to showing keywords of a subreddit instead of users
        '''
        self.users_btn['state'] = NORMAL
        self.keywords_btn['state'] = DISABLED

        self.data_List.heading("one", text="keyword")
        self.data_List.heading("two", text="score")  

        self.ip_ban_btn.destroy()
        self.user_ban_btn.destroy()
        self.warning_btn.destroy()
        self.warning_txt_entry.destroy()

        self.add_keyword_btn = ttk.Button(self.admin_btn_frame, width=8, text='add', command=self.add_keyword, state=NORMAL)
        self.add_keyword_btn.pack(side=LEFT, padx=(0, 20))

        self.del_keword_btn = ttk.Button(self.admin_btn_frame, width=8, text='delete', command=self.del_keyword, state=NORMAL)
        self.del_keword_btn.pack(side=LEFT, padx=(20, 0))

        self.req_subr_keywords()


    def switch_to_subr_users(self):
        '''
        switch to showing users of a subreddit instead of keywords
        '''
        self.users_btn['state'] = DISABLED
        self.keywords_btn['state'] = NORMAL

        self.data_List.heading("one", text="user")
        self.data_List.heading("two", text="time")  

        self.add_keyword_btn.destroy()
        self.del_keword_btn.destroy()

        self.ip_ban_btn = ttk.Button(self.admin_btn_frame, width=8, text='ip ban', state=NORMAL, command=self.ip_ban)
        self.ip_ban_btn.pack(side=LEFT, padx=(0, 20))

        self.user_ban_btn = ttk.Button(self.admin_btn_frame, width=8, text='ban user', command=self.ban_user, state=NORMAL)
        self.user_ban_btn.pack(side=LEFT, padx=(20))

        self.warning_txt_entry = ttk.Entry(self.admin_btn_frame, width=25)
        self.warning_txt_entry.pack(side=LEFT, padx=(20, 0))

        self.warning_btn = ttk.Button(self.admin_btn_frame, width=8, text='warning', command=self.send_warning, state=NORMAL, style='Accent.TButton')
        self.warning_btn.pack(side=LEFT, padx=(5, 0))

        self.req_subr_users()


    def admin_subr_info(self, data):
        '''
        subreddit management and content page
        '''
        self.destroy_admin_info()

        # organize subreddit data
        data = data.split(';')
        subr = data[0].split(':')
        data.pop(0)
        user_lst = eval(data.pop(0))
        self.current_subr_name = subr[0]

        self.users_frame = Frame(self.canvas_frame, bg='white')
        self.users_frame.pack(pady=(0, 50))

        self.subr_frame = Frame(self.users_frame, bg='white')
        self.subr_frame.pack(anchor=W)

        self.subr_name = Label(self.subr_frame, text=f'r/{subr[0]}', bg='white', font='roboto 14 bold')
        self.subr_name.pack(pady=(20, 10), anchor=W)

        self.subr_des = Label(self.subr_frame, text=subr[1], bg='white', font='roboto 12')
        self.subr_des.pack(pady=(0, 50), anchor=W)

        user_keyword_frame = Frame(self.users_frame, bg='white')
        user_keyword_frame.pack(pady=(0, 15))

        self.users_btn = ttk.Button(user_keyword_frame, width=9, text='users', command=self.switch_to_subr_users, state=DISABLED)
        self.users_btn.pack(side=LEFT, padx=(0, 20))

        self.keywords_btn = ttk.Button(user_keyword_frame, width=9, text='keywords', command=self.switch_to_subr_keywords, state=NORMAL)
        self.keywords_btn.pack(side=LEFT, padx=(20, 0))

        self.lb_frame = Frame(self.users_frame, bg='white')
        self.lb_frame.pack()

        scrollbar = ttk.Scrollbar(self.lb_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        style.configure('mystyle.Treeview', highlightthickness=0)

        self.data_List = ttk.Treeview(self.lb_frame, yscrollcommand=scrollbar.set, height=15, style='mystyle.Treeview', columns=('one', 'two'))
        self.data_List.pack()

        self.data_List.column('#0', width=0, stretch=NO)
        self.data_List.column('one', width=270)
        self.data_List.column('two', width=270)

        self.data_List.heading("one", text="user")
        self.data_List.heading("two", text="time")  

        scrollbar.config(command=self.data_List.yview)

        for user in user_lst:
            self.data_List.insert(parent='', index=END,  text='', values=user)

        self.admin_btn_frame = Frame(self.users_frame, bg='white')
        self.admin_btn_frame.pack(pady=(10, 0))

        self.ip_ban_btn = ttk.Button(self.admin_btn_frame, width=9, text='ip ban', command=self.ip_ban, state=NORMAL)
        self.ip_ban_btn.pack(side=LEFT, padx=(0, 20))

        self.user_ban_btn = ttk.Button(self.admin_btn_frame, width=9, text='ban user', command=self.ban_user, state=NORMAL)
        self.user_ban_btn.pack(side=LEFT, padx=(20))

        self.warning_txt_entry = ttk.Entry(self.admin_btn_frame, width=25)
        self.warning_txt_entry.pack(side=LEFT, padx=(20, 0))

        self.warning_btn = ttk.Button(self.admin_btn_frame, width=9, text='warning', command=self.send_warning, state=NORMAL, style='Accent.TButton')
        self.warning_btn.pack(side=LEFT, padx=(5, 0))

        # list of subreddit posts
        posts =[]
        for post in data:
            post = post.split(':')
            posts.append({"_id": post[0], "is_img": post[1], "user": post[2], "title": post[3], "content": post[4], "date": post[5]})

        self.posts_frame = Frame(self.canvas_frame, bg='white')
        self.posts_frame.pack()

        r = StringVar()

        for post in posts:
            post_frame = ttk.Frame(self.posts_frame, style='Card.TFrame')
            post_frame.pack(pady=(0, 20))

            post_frame2 = Frame(post_frame)
            post_frame2.pack(pady=5, padx=20, expand=YES)

            Label(post_frame2, text=f'posted by u/{post["user"]}     {post["date"]}', font='roboto 8').pack(anchor=W)
            Label(post_frame2, text=post["title"], font='roboto 18 bold').pack(anchor=W)
            Label(post_frame2).pack(anchor=W, padx=(0, 550))

            if post["is_img"] == 'False':

                txt = post["content"].replace('\\n', '\n')
                Label(post_frame2, text=txt, font='roboto 12', justify=LEFT, wraplength=500).pack(anchor=W, pady=(10, 0))
            
            else:
                self.img_lable = Label(post_frame2, bg='white')
                self.img_lable.pack(anchor=W)
        
                img = base64.b64decode(post["content"] + '==')
                with open('show_img.jpg', 'wb') as obj:
                    obj.write(img)

                img = Image.open('show_img.jpg')
                my_image = ImageTk.PhotoImage(img)
        
                h = my_image.height()
                w = my_image.width()
        
                # get ratio between width and height of image
                if h > w:
                    ratio = (float(w)/float(h), 1)
                else:
                    ratio = (1, float(h)/float(w))

                # max image height and width is 400
                resized_image = img.resize((int(ratio[0]*400),int(ratio[1]*400)), Image.ANTIALIAS)
                my_image = ImageTk.PhotoImage(resized_image)
        
                self.img_lable.image = my_image
                self.img_lable.configure(image=my_image)

            radio_img_path = str(os.path.dirname(os.path.abspath(__file__))) + r'\\radio_img\\radio_blue.png'
            photo = PhotoImage(file=radio_img_path)
            view_btn = Radiobutton(post_frame2, width=116, height=34, command=lambda: self.get_comments_by_id(r.get()), var=r, value=str(post), indicatoron=0, image=photo, borderwidth=0, highlightthickness=0, highlightbackground='#fefefe', highlightcolor='#fefefe')
            view_btn.image = photo
            view_btn.pack(anchor=W, pady=(20, 20))

        root.geometry(f'{root.winfo_width() + 1}x{root.winfo_height()}+{root.winfo_x()}+{root.winfo_y()}')

        self.start_req_thread(self.get_subr_users)


    def show_current_settings(self, ngram, dup, profanity):
        '''
        show current settings to admin
        '''
        self.ngram_size_entry.insert(0, ngram)
        self.duplication_threshold_entry.insert(0, dup)
        self.profanity_option.set(profanity)


    def algorithm_settings(self):
        '''
        admin settings page
        '''
        try:
            # if user is admin and request thread exists stop thread
            if self.last_update_time:
                self.last_update_time = time.time() + 1000.0
        except AttributeError:
            pass

        self.info_frame.destroy()
        self.info_frame = Frame(self.main_frame, bg='white')
        self.info_frame.pack()

        Label(self.info_frame, text='keywords', font='roboto 16 bold', bg='white').pack(pady=(20, 0), anchor=W)

        Label(self.info_frame, text='max ngram size:', font='roboto 12', bg='white').pack(pady=(20,5), anchor=W)

        self.ngram_size_entry = ttk.Entry(self.info_frame,  width=5)
        self.ngram_size_entry.pack(anchor=W)

        apply_btn = ttk.Button(self.info_frame, width=6, text='apply', command=self.change_max_ngram_size, style='Accent.TButton')
        apply_btn.pack(pady=(10), anchor=W)

        Label(self.info_frame, text='duplication threshold:', font='roboto 12', bg='white').pack(pady=(20,5), anchor=W)

        self.duplication_threshold_entry = ttk.Entry(self.info_frame, width=5)
        self.duplication_threshold_entry.pack(anchor=W)

        apply_btn = ttk.Button(self.info_frame, width=6, text='apply', command=self.change_duplication_threshold, style='Accent.TButton')
        apply_btn.pack(pady=(10), anchor=W)

        Label(self.info_frame, text='* values range from 0.1 to 0.9, bigger number means more duplication', font='roboto 8', bg='white').pack(anchor=W, pady=(0, 50))

        Label(self.info_frame, text='profanity', font='roboto 16 bold', bg='white').pack(pady=(20, 0), anchor=W)

        Label(self.info_frame, text='automatically censor, block or allow profanity', font='roboto 12', bg='white').pack(pady=(20,0), anchor=W)
        
        style.configure('Wild.TRadiobutton',    
        background='white')  

        self.profanity_option = StringVar()
        censor_option = ttk.Radiobutton(self.info_frame, text="censor", variable=self.profanity_option, value='censor', style='Wild.TRadiobutton')
        censor_option.pack(anchor=W)

        block_option = ttk.Radiobutton(self.info_frame, text="block", variable=self.profanity_option, value='block', style='Wild.TRadiobutton')
        block_option.pack(anchor=W)

        censor_option = ttk.Radiobutton(self.info_frame, text="allow", variable=self.profanity_option, value='allow', style='Wild.TRadiobutton')
        censor_option.pack(anchor=W)

        apply_btn = ttk.Button(self.info_frame, width=6, text='apply', command=self.change_profanity_approach, style='Accent.TButton')
        apply_btn.pack(pady=(10), anchor=W)
        
        self.get_current_settings()


    def admin_main_page(self):
        '''
        admin menu
        '''
        try:
            self.on_closing()
        except TclError:
            pass

        self.main_frame.destroy()

        self.my_menu = Menu(root)
        root.config(menu=self.my_menu)
        self.create_menu = Menu(self.my_menu)

        self.my_menu.add_cascade(label='administration', menu=self.create_menu)
        self.create_menu.add_command(label='subreddit', command=self.subr_administration)
        self.create_menu.add_command(label='users', command=self.active_user_information)
        self.create_menu.add_command(label='algorithms', command=self.algorithm_settings)

        self.main_frame = Frame(root, background='white')
        self.main_frame.pack(fill=BOTH, expand=TRUE)

        self.top_bar2 = Frame(self.main_frame, background='white')
        self.top_bar2.pack(fill=X)

        self.display_name = Label(self.top_bar2, text=self.username, font='roboto 14 bold')
        self.display_name.pack(side=RIGHT, padx=(15, 200), pady=(50, 0))

        self.info_frame = Frame(self.main_frame, background='white')
        self.info_frame.pack()


    def active_user_information(self):
        '''
        page showing all users in subreddits and their time in them
        '''
        try:
            # if user is admin and request thread exists stop thread
            if self.last_update_time:
                self.last_update_time = time.time() + 1000.0
        except AttributeError:
            pass

        self.info_frame.destroy()
        self.info_frame = Frame(self.main_frame)
        self.info_frame.pack()

        self.lb_frame = Frame(self.info_frame)
        self.lb_frame.pack()

        scrollbar = ttk.Scrollbar(self.lb_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.data_List = Listbox(self.lb_frame, yscrollcommand=scrollbar.set, height=20, width=100, font='roboto 10', relief='flat', highlightthickness=0)
        self.data_List.pack()

        scrollbar.config(command=self.data_List.yview)
        
        self.start_req_thread(self.get_all_active_users)
        self.get_all_active_users()


    def subr_administration(self):
        '''
        page for information and management of all subreddits (admin)
        '''
        self.info_frame.destroy()
        self.info_frame = Frame(self.main_frame, bg='white')
        self.info_frame.pack()

        self.lb_frame = Frame(self.info_frame, bg='white')
        self.lb_frame.pack()

        scrollbar = ttk.Scrollbar(self.lb_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        style.configure('mystyle.Treeview', highlightthickness=0)

        self.data_List = ttk.Treeview(self.lb_frame, yscrollcommand=scrollbar.set, height=15, style='mystyle.Treeview', columns=('one', 'two'))
        self.data_List.pack()

        self.data_List.column('#0', width=0, stretch=NO)
        self.data_List.column('one', width=325)
        self.data_List.column('two', width=325)

        self.data_List.heading("one", text="community")
        self.data_List.heading("two", text="number of users")

        scrollbar.config(command=self.data_List.yview)
        
        keyword_frame = Frame(self.info_frame, bg='white')
        keyword_frame.pack(pady=15)

        self.keyword_entry = ttk.Entry(keyword_frame,  width=25)
        self.keyword_entry.pack(side=LEFT, padx=(0, 20))

        keyword_btn = ttk.Button(keyword_frame, width=14, text='sort by keyword', command=self.req_subrs_keyword, style='Accent.TButton')
        keyword_btn.pack(side=LEFT)

        self.keyword_entry.bind('<Return>', self.req_subrs_keyword)

        btn_frame = Frame(self.info_frame, bg='white')
        btn_frame.pack(pady=(0, 10))

        self.date_btn = ttk.Button(btn_frame, width=18, text='sort by date', command=self.req_subrs_date, state=NORMAL)
        self.date_btn.pack(side=LEFT, padx=(0, 20))

        self.user_num_btn = ttk.Button(btn_frame, width=18, text='sort by user amount', command=self.req_subrs_users, state=DISABLED)
        self.user_num_btn.pack(side=LEFT, padx=(20))

        self.community_details_btn = ttk.Button(btn_frame, width=18, text='community details', command=self.get_admin_community, state=NORMAL)
        self.community_details_btn.pack(side=LEFT, padx=(20))

        self.community_details_btn = ttk.Button(btn_frame, width=18, text='change date', command=self.change_date_page, state=NORMAL)
        self.community_details_btn.pack(side=LEFT, padx=(20, 0))

        self.display_name.config(bg='white')

        # try to switch refresh request type. in case request thread in not running start it
        try:
            self.req_subrs_users()
        except AttributeError:
            self.get_admin_subrs_users()
            self.start_req_thread(self.get_admin_subrs_users)


    def destroy_root2(self):
        '''
        destroy popup
        '''
        self.root2.destroy()
        self.send_btn['state'] = NORMAL


    def subr_alert(self, subr_name):
        '''
        alert when user tries to create subreddit and a similar subreddit already exists
        '''
        self.send_btn['state'] = DISABLED

        self.root2 = Tk()
        self.root2.geometry('500x410+400+200')
        self.root2.minsize(300, 410)
        self.root2.update()
        self.root2.configure(background='white')

        # add sv_ttk theme to popup
        sv_ttk_path = str(sv_ttk.__file__).replace(r'\__init__.py', '')
        self.root2.call("source", fr"{sv_ttk_path}\sun-valley.tcl")
        self.root2.call("set_theme", "light")

        self.main_frame2 = Frame(self.root2, background='white')
        self.main_frame2.pack()

        alert_prompt = Label(self.main_frame2, text=f'a similar community r/{subr_name} already exists.\nare you sure about creating the community?', font='roboto 12', background='white', justify=LEFT)
        alert_prompt.pack(pady=(30, 0), anchor=W)

        btn_frame = Frame(self.main_frame2, background='white')
        btn_frame.pack()

        self.yes_btn = ttk.Button(btn_frame, width=4, text='yes', command=self.new_community_after_alert)
        self.yes_btn.pack(padx=(0, 10), pady=(50, 20), side=LEFT)

        self.no_btn = ttk.Button(btn_frame, width=4, text='no', command=self.destroy_root2)
        self.no_btn.pack(padx=(10, 0), pady=(50, 20), side=LEFT)

        self.root2.mainloop()


    def select_img(self):
        '''
        select image file and display image
        '''
        self.img_file = fd.askopenfilename(title='select an image',  filetypes=[('jpg files', '*.jpg')])
        img = Image.open(self.img_file)
 
        my_image = ImageTk.PhotoImage(img)

        h = my_image.height()
        w = my_image.width()

        # get ratio between width and height of image
        if h > w:
            ratio = (float(w)/float(h), 1)
        else:
            ratio = (1, float(h)/float(w))

        # max image width and height 300
        resized_image = img.resize((int(ratio[0]*300),int(ratio[1]*300)), Image.ANTIALIAS)
        my_image = ImageTk.PhotoImage(resized_image)

        self.image_lable.image = my_image
        self.image_lable.configure(image=my_image)

        self.select_img_btn.destroy()


    def destroy_content(self):
        '''
        destroy previous page. create canvas with scrollbar
        '''
        self.search_frame.destroy()
        self.content_frame.destroy()

        self.search_frame = Frame(self.main_frame)
        self.search_frame.pack(pady=(0, 20))

        self.search_prompt = Label(self.search_frame, text='search for subreddit')
        self.search_prompt.pack(anchor = W)

        self.search_entry = ttk.Entry(self.search_frame, width=100)
        self.search_entry.pack(pady=(15, 0))

        self.content_frame = Frame(self.main_frame, background='white')
        self.content_frame.pack(fill=BOTH, expand=YES)

        self.my_canvas = Canvas(self.content_frame, bg='white', relief=FLAT, highlightthickness=0)
        self.my_canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        self.canvas_frame = Frame(self.my_canvas, bg='white', width=self.my_canvas.winfo_width())
        self.canvas_window = self.my_canvas.create_window((0, 0), window=self.canvas_frame, anchor=NW)

        yscrollbar = ttk.Scrollbar(self.content_frame, orient='vertical', command=self.my_canvas.yview)
        yscrollbar.pack(side=RIGHT, fill=Y)

        self.my_canvas.configure(yscrollcommand=yscrollbar.set)

        self.my_canvas.bind('<Configure>', lambda e: self.my_canvas.configure(scrollregion=self.my_canvas.bbox('all')))

        canvas_width = root.winfo_width() 
        self.my_canvas.itemconfig(self.canvas_window, width = canvas_width)

        self.search_entry.bind('<Return>', self.find_subreddit)
        self.main_frame.bind('<Configure>', self.frame_width)


    def img_post(self):
        '''
        image post creation page
        '''
        self.search_frame.destroy()
        self.content_frame.destroy()
        self.content_frame = Frame(self.main_frame, background='white')
        self.content_frame.pack()

        self.buttons_frame = Frame(self.content_frame, background='white')
        self.buttons_frame.pack()

        self.txt_btn = ttk.Button(self.buttons_frame, width=8, text='text', command=self.create_post, state=NORMAL, style='Toggle.TButton')
        self.txt_btn.pack(side=LEFT, padx=(0, 15), pady=(50, 0))

        self.img_btn = ttk.Button(self.buttons_frame, width=8, text='image', command=self.img_post, state=DISABLED, style='Toggle.TButton')
        self.img_btn.pack(side=LEFT, padx=(15), pady=(50, 0))

        self.subr_prompt = Label(self.content_frame, text='subreddit:', font='roboto 12', background='white')
        self.subr_prompt.pack(pady=(50, 0), anchor=W)

        self.subr_entry = ttk.Entry(self.content_frame, width=116)
        self.subr_entry.pack(pady=(15, 0), anchor=W)

        self.title_prompt = Label(self.content_frame, text='title:', font='roboto 12', background='white')
        self.title_prompt.pack(pady=(50, 0), anchor=W)

        self.title_entry = ttk.Entry(self.content_frame, width=116)
        self.title_entry.pack(pady=(15, 0), anchor=W)

        self.select_img_btn = ttk.Button(self.content_frame, width=14, text='choose image', command=self.select_img)
        self.select_img_btn.pack(pady=(50, 0))

        self.image_lable = Label(self.content_frame, bg='white')
        self.image_lable.pack(pady=(20, 0))

        self.send_btn = ttk.Button(self.content_frame, width=11, text='create post', command=self.send_img_post, style='Accent.TButton')
        self.send_btn.pack(pady=(30, 0))


    def create_post(self):
        '''
        text post creation page
        '''
        self.display_name.config(bg='white')
        self.main_frame.config(bg='white')
        self.top_bar.config(bg='white')

        self.search_frame.destroy()
        self.content_frame.destroy()
        self.content_frame = Frame(self.main_frame, background='white')
        self.content_frame.pack()

        self.buttons_frame = Frame(self.content_frame, background='white')
        self.buttons_frame.pack()

        self.txt_btn = ttk.Button(self.buttons_frame, width=8, text='text', command=self.create_post, state=DISABLED, style='Toggle.TButton')
        self.txt_btn.pack(side=LEFT, padx=(0, 15), pady=(50, 0))

        self.img_btn = ttk.Button(self.buttons_frame, width=8, text='image', command=self.img_post, state=NORMAL, style='Toggle.TButton')
        self.img_btn.pack(side=LEFT, padx=(15), pady=(50, 0))

        self.subr_prompt = Label(self.content_frame, text='subreddit:', font='roboto 12', background='white')
        self.subr_prompt.pack(pady=(50, 0), anchor=W)

        self.subr_entry = ttk.Entry(self.content_frame, width=116)
        self.subr_entry.pack(pady=(15, 0), anchor=W)

        self.title_prompt = Label(self.content_frame, text='title:', font='roboto 12', background='white')
        self.title_prompt.pack(pady=(50, 0), anchor=W)

        self.title_entry = ttk.Entry(self.content_frame, width=116)
        self.title_entry.pack(pady=(15, 0), anchor=W)

        self.txt_prompt = Label(self.content_frame, text='text:', font='roboto 12', background='white')
        self.txt_prompt.pack(pady=(50, 0), anchor=W)

        self.txt_entry = Text(self.content_frame, width=75, height=5, border='1', font='roboto 14', bg='white')
        self.txt_entry.pack(pady=(15, 0), anchor=W)

        self.send_btn = ttk.Button(self.content_frame, width=11, text='create post', command=self.send_txt_post, style='Accent.TButton')
        self.send_btn.pack(pady=(50, 0))

        self.in_home_page()


    def create_community(self):
        self.display_name.config(bg='white')
        self.main_frame.config(bg='white')
        self.top_bar.config(bg='white')

        self.search_frame.destroy()
        self.content_frame.destroy()
        self.content_frame = Frame(self.main_frame, background='white')
        self.content_frame.pack()

        self.comm_name_entry = Label(self.content_frame, text='enter community name', font='roboto 12', background='white')
        self.comm_name_entry.pack(pady=(50, 0), anchor=W)

        self.comm_name_entry = ttk.Entry(self.content_frame, width=40)
        self.comm_name_entry.pack(pady=(15, 0), anchor=W)

        self.description_prompt = Label(self.content_frame, text='enter community description', font='roboto 12', background='white')
        self.description_prompt.pack(pady=(50, 0), anchor=W)

        self.description_entry = ttk.Entry(self.content_frame, width=40)
        self.description_entry.pack(pady=(15, 0), anchor=W)

        self.warning_lable = Label(self.content_frame, text='', bg='white')
        self.warning_lable.pack(anchor=W)

        self.send_btn = ttk.Button(self.content_frame, width=15, text='create community', command=self.send_new_community, style='Accent.TButton', state=NORMAL)
        self.send_btn.pack(pady=(30, 0))

        self.in_home_page()


    def logged_in(self):
        '''
        after user logged in add menu and show username
        '''
        self.top_bar.config(bg='#fefefe')
        try:
            self.display_name.config(bg='#fefefe')
        except AttributeError:
            pass

        try:
            self.on_closing()
        except RuntimeError:
            pass
        except TclError:
            pass

        self.main_frame.destroy()

        self.my_menu = Menu(root)
        root.config(menu=self.my_menu)
        self.create_menu = Menu(self.my_menu)
        self.my_menu.add_cascade(label='pages', menu=self.create_menu)
        self.create_menu.add_command(label='home page', command=self.logged_in)

        self.create_menu.add_separator()

        self.create_menu.add_command(label='create community', command=self.create_community)
        self.create_menu.add_command(label='create post', command=self.create_post)

        self.main_tk()

        self.login_btn.destroy()
        self.signup_btn.destroy()

        self.display_name = Label(self.top_bar, text=self.username, font='roboto 14 bold')
        self.display_name.pack(side=RIGHT, padx=(15, 200), pady=(50, 0))

        self.in_home_page()


    def on_closing(self):
        '''
        if user closes popup return login_btn and signup_btn to normal
        '''
        self.root2.destroy()
        self.login_btn['state'] = NORMAL
        self.signup_btn['state'] = NORMAL


    def signup(self):
        '''
        sign up popup
        '''
        self.login_btn['state'] = DISABLED
        self.signup_btn['state'] = DISABLED

        self.root2 = Tk()
        self.root2.geometry('500x410+400+200')
        self.root2.minsize(300, 410)
        self.root2.update()
        self.root2.configure(background='white')

        self.root2.protocol("WM_DELETE_WINDOW", self.on_closing)

        # add sv_ttk theme to popup
        sv_ttk_path = str(sv_ttk.__file__).replace(r'\__init__.py', '')
        self.root2.call("source", fr"{sv_ttk_path}\sun-valley.tcl")
        self.root2.call("set_theme", "light")

        self.main_frame2 = Frame(self.root2, background='white')
        self.main_frame2.pack()

        self.name_prompt = Label(self.main_frame2, text='enter user name', font='roboto 12', background='white')
        self.name_prompt.pack(pady=(50, 0), anchor=W)

        self.name_entry = ttk.Entry(self.main_frame2, width=40)
        self.name_entry.pack(pady=(15, 0), anchor=W)

        self.pass_prompt = Label(self.main_frame2, text='enter password', font='roboto 12', background='white')
        self.pass_prompt.pack(pady=(50, 0), anchor=W)

        self.pass_entry = ttk.Entry(self.main_frame2, width=40)
        self.pass_entry.pack(pady=(15, 0), anchor=W)

        self.send_btn = ttk.Button(self.main_frame2, width=6, text='sign up', command=self.send_signup, style='Accent.TButton')
        self.send_btn.pack(pady=(50, 0))

        self.root2.mainloop()


    def banned_user(self):
        self.main_frame2.destroy()
        Label(self.root2, text='cant login, user is banned', bg='white', font='roboto 16').pack(pady=(75,0))


    def login(self):
        '''
        log in popup
        '''
        self.login_btn['state'] = DISABLED
        self.signup_btn['state'] = DISABLED

        self.root2 = Tk()
        self.root2.geometry('500x410+400+200')
        self.root2.minsize(300, 410)
        self.root2.update()
        self.root2.configure(background='white')

        # add sv_ttk theme to popup
        sv_ttk_path = str(sv_ttk.__file__).replace(r'\__init__.py', '')
        self.root2.call("source", fr"{sv_ttk_path}\sun-valley.tcl")
        self.root2.call("set_theme", "light")

        self.root2.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.main_frame2 = Frame(self.root2, background='white')
        self.main_frame2.pack()

        self.name_prompt = Label(self.main_frame2, text='enter user name', font='roboto 12', background='white')
        self.name_prompt.pack(pady=(50, 0), anchor=W)

        self.name_entry = ttk.Entry(self.main_frame2, width=40)
        self.name_entry.pack(pady=(15, 0), anchor=W)

        self.pass_prompt = Label(self.main_frame2, text='enter password', font='roboto 12', background='white')
        self.pass_prompt.pack(pady=(50, 0), anchor=W)

        self.pass_entry = ttk.Entry(self.main_frame2, width=40)
        self.pass_entry.pack(pady=(15, 0), anchor=W)

        self.send_btn = ttk.Button(self.main_frame2, width=6, text='log in', command=self.send_login, style='Accent.TButton')
        self.send_btn.pack(pady=(50, 0))

        self.root2.mainloop()


    def main_tk(self):
        '''
        first page when client connects (before login)
        '''
        self.main_frame = Frame(root)
        self.main_frame.pack(fill=BOTH, expand=TRUE)

        self.top_bar = Frame(self.main_frame)
        self.top_bar.pack(fill=X)

        self.login_btn = ttk.Button(self.top_bar, width=6, text='log in', command=self.login, state='normal')
        self.login_btn.pack(side=RIGHT, padx=(15, 200), pady=(20, 0))

        self.signup_btn = ttk.Button(self.top_bar, width=6, text='sign up', command=self.signup, state='normal', style='Accent.TButton')
        self.signup_btn.pack(side=RIGHT, padx=(15), pady=(20, 0))

        self.search_frame = Frame(self.main_frame)
        self.search_frame.pack(pady=(0, 20))

        self.search_prompt = Label(self.search_frame, text='search for subreddit', font='roboto 12')
        self.search_prompt.pack(anchor = W)

        self.search_entry = ttk.Entry(self.search_frame, width=100)
        self.search_entry.pack(pady=(15, 0))

        self.content_frame = Frame(self.main_frame, background='white')
        self.content_frame.pack(fill=BOTH, expand=YES)

        self.my_canvas = Canvas(self.content_frame, bg='white', relief=FLAT, highlightthickness=0)
        self.canvas_frame = Frame(self.my_canvas, bg='white', width=self.my_canvas.winfo_width())
        yscrollbar = ttk.Scrollbar(self.content_frame, orient='vertical', command=self.my_canvas.yview)
        self.my_canvas.configure(yscrollcommand=yscrollbar.set)

        yscrollbar.pack(side=RIGHT, fill=Y)
        self.my_canvas.pack(side=LEFT, fill=BOTH, expand=YES)         
        self.canvas_window = self.my_canvas.create_window((0, 0), window=self.canvas_frame, anchor=NW)
        self.canvas_frame.bind('<Configure>', lambda e: self.my_canvas.configure(scrollregion=self.my_canvas.bbox('all')))

        canvas_width = root.winfo_width()
        self.my_canvas.itemconfig(self.canvas_window, width = canvas_width)

        self.search_entry.bind('<Return>', self.find_subreddit)
        self.main_frame.bind('<Configure>', self.frame_width)


    def view_discussion(self, post, comments):
        '''
        view post and comments
        '''
        try:
            # if user is admin and request thread exists stop thread
            if self.last_update_time:
                self.last_update_time = time.time() + 1000.0
        except AttributeError:
            pass

        if self.is_admin:
            self.destroy_admin_info()
        else:
            self.destroy_content()

        disc_frame = Frame(self.canvas_frame, bg='white')
        disc_frame.pack()

        Label(disc_frame, bg='white').pack(anchor=W)

        post_frame1 = Frame(disc_frame)
        post_frame1.pack()

        post_frame = ttk.Frame(post_frame1, style='Card.TFrame')
        post_frame.pack()

        Label(post_frame, text=f'posted by u/{post["user"]}     {post["date"]}', font='roboto 8').pack(anchor=W, pady=(10, 0), padx=(15, 0))
        Label(post_frame, text=post["title"], font='roboto 18 bold').pack(anchor=W,padx=(15, 0))
        Label(post_frame).pack(anchor=W, padx=(15, 583))
        
        # show text post
        if not post["is_img"]:
            Label(post_frame, text=post["content"].replace('\\n', '\n'), font='roboto 12', justify=LEFT, wraplength=560).pack(anchor=W, pady=(0, 10),padx=(15, 0))

        # show image post
        else:
            self.img_lable = Label(post_frame)
            self.img_lable.pack(anchor=W, pady=(0, 10),padx=(15, 0))
    
            img = base64.b64decode(post["content"])
            with open('show_img.jpg', 'wb') as obj:
                obj.write(img)
            img = Image.open('show_img.jpg')
            my_image = ImageTk.PhotoImage(img)
    
            h = my_image.height()
            w = my_image.width()
    
            # get ratio between width and height of image
            if h > w:
                ratio = (float(w)/float(h), 1)
            else:
                ratio = (1, float(h)/float(w))

            # max image height and width is 565
            resized_image = img.resize((int(ratio[0]*565),int(ratio[1]*565)), Image.ANTIALIAS)
            my_image = ImageTk.PhotoImage(resized_image)
    
            self.img_lable.image = my_image
            self.img_lable.configure(image=my_image)
        
        self.comments_frame = Frame(disc_frame, background='white')
        self.comments_frame.pack(anchor = W)

        try:
            if self.username and not self.is_admin:
                comment_entry_frame = Frame(self.comments_frame, background='white')
                comment_entry_frame.pack(anchor = W)

                self.comment_entry = Text(comment_entry_frame, height=2, width=55, border='1', font='roboto 12', relief=SOLID)
                self.comment_entry.pack(pady=(15, 10), padx=(0, 20), side=LEFT)

                self.send_btn = ttk.Button(comment_entry_frame, width=8, text='comment', command=lambda: self.new_comment(post['_id']), style='Accent.TButton')
                self.send_btn.pack(pady=(15, 10), side=LEFT)

        except AttributeError:
            # in case user is not logged in he cant comment
            self.search_prompt = Label(self.comments_frame, text='log in or sign up to comment', font='roboto 12', background='white')
            self.search_prompt.pack(anchor = W, pady=(20, 50))

        if comments:
            # show comments of post
            for com in comments:
                com = eval(com)
                self.comment_frame = Frame(self.comments_frame, background='white')
                self.comment_frame.pack()

                Label(self.comment_frame, bg='white').pack(anchor=W, padx=(0, 550))
                Label(self.comment_frame, text=f'posted by u/{com["user"]}     {com["date"]}', font='roboto 8', bg='white').pack(anchor=W)
                Label(self.comment_frame, text=com["text"].replace('\\n', '\n'), font='roboto 12', justify=LEFT, wraplength=500, bg='white').pack(anchor=W, pady=(10, 0))
        root.geometry(f'{root.winfo_width() + 1}x{root.winfo_height()}+{root.winfo_x()}+{root.winfo_y()}')
        

    def display_subr(self, content):
        '''
        show subreddit posts
        '''
        self.destroy_content()

        content = content.split(';')
        subr = content[0].split(':')
        content.pop(0)

        posts =[]
        for post in content:
            post = post.split(':')
            posts.append({"_id": post[0], "is_img": post[1], "user": post[2], "title": post[3], "content": post[4], "date": post[5]})
        
        self.posts_frame = Frame(self.canvas_frame, bg='white')
        self.posts_frame.pack()

        self.subr_frame = Frame(self.posts_frame, bg='white')
        self.subr_frame.pack(anchor=W)

        self.subr_name = Label(self.subr_frame, text=f'r/{subr[0]}', bg='white', font='roboto 14 bold')
        self.subr_name.pack(pady=(20, 10), anchor=W)

        self.subr_des = Label(self.subr_frame, text=subr[1], font='roboto 12', bg='white')
        self.subr_des.pack(pady=(0, 50), anchor=W)

        r = StringVar()

        for post in posts:
            post_frame = ttk.Frame(self.posts_frame, style='Card.TFrame')
            post_frame.pack(pady=(0, 20))

            post_frame2 = Frame(post_frame)
            post_frame2.pack(pady=5, padx=20, expand=YES)

            Label(post_frame2, text=f'posted by u/{post["user"]}     {post["date"]}', font='roboto 8').pack(anchor=W)
            Label(post_frame2, text=post["title"], font='roboto 18 bold').pack(anchor=W)
            Label(post_frame2).pack(anchor=W, padx=(0, 550))

            # show text post
            if post["is_img"] == 'False':

                txt = post["content"].replace('\\n', '\n')
                Label(post_frame2, text=txt, font='roboto 12', justify=LEFT, wraplength=500).pack(anchor=W)
            
            # show image post
            else:
                self.img_lable = Label(post_frame2)
                self.img_lable.pack(anchor=W)

                img = base64.b64decode(str(post["content"]))
                with open('show_img.jpg', 'wb') as obj:
                    obj.write(img)

                img = Image.open('show_img.jpg')
                my_image = ImageTk.PhotoImage(img)
        
                h = my_image.height()
                w = my_image.width()
        
                # get ratio between width and height of image
                if h > w:
                    ratio = (float(w)/float(h), 1)
                else:
                    ratio = (1, float(h)/float(w))
        
                # max image height and width is 400
                resized_image = img.resize((int(ratio[0]*400),int(ratio[1]*400)), Image.ANTIALIAS)
                my_image = ImageTk.PhotoImage(resized_image)
        
                self.img_lable.image = my_image
                self.img_lable.configure(image=my_image)
            
            radio_img_path = str(os.path.dirname(os.path.abspath(__file__))) + r'\\radio_img\\radio_blue.png'
            photo = PhotoImage(file=radio_img_path)
            view_btn = Radiobutton(post_frame2, width=116, height=34, command=lambda: self.get_comments_by_id(r.get()), var=r, value=str(post), indicatoron=0, image=photo, borderwidth=0, highlightthickness=0, highlightbackground='#fefefe', highlightcolor='#fefefe')
            view_btn.image = photo
            view_btn.pack(anchor=W, pady=(20, 20))

            root.geometry(f'{root.winfo_width() + 1}x{root.winfo_height()}+{root.winfo_x()}+{root.winfo_y()}')


    def show_subr_results(self, subr_lst):
        '''
        subreddit search results
        '''
        self.destroy_content()

        r = StringVar()
        for subr in subr_lst:
            subrs_frame = Frame(self.canvas_frame, bg='white')
            subrs_frame.pack()
            
            Label(subrs_frame, bg='white').pack(padx=(0, 500), anchor=W)
            Label(subrs_frame, text=f'r/{subr["name"]}', font='roboto 12', bg='white').pack(anchor=W, pady=(0, 10))
            Label(subrs_frame, text=subr['description'], font='roboto 12', justify=LEFT, wraplength=500, bg='white').pack(anchor=W, pady=(0, 10))
            
            radio_img_path = str(os.path.dirname(os.path.abspath(__file__))) + r'\\radio_img\\radio_grey.png'
            photo = PhotoImage(file=radio_img_path)
            view_btn = Radiobutton(subrs_frame, width=120, height=34, command=lambda: self.get_subreddit_page('r/' + r.get()), var=r, value=str(subr["name"]), indicatoron=0, image=photo, borderwidth=0, highlightthickness=0, bg='white', highlightbackground='white', highlightcolor='white')
            view_btn.image = photo
            view_btn.pack(anchor=W, pady=(20, 20))

        self.in_home_page()


    def handler(self):
        '''
        recieve data from server
        '''
        self.IP = sock.getsockname()[0]
        self.is_admin = False
        while True:
            try:
                recv = sock.recv(BUFF)
                if not recv:
                    break
                recv = recv.decode()

                if re.match(r'(signup|login) good:.+:.+', recv):
                    recv = recv.split(':')
                    self.username = recv[1]
                    # check if user is admin
                    if recv[2] == 'True':
                        self.is_admin = True
                        self.admin_main_page()
                        self.subr_administration()
                    elif recv[2] == 'False': 
                        self.logged_in()

                elif re.match(r'(\d+)subr_page:(.+)', recv):
                    # subreddit information

                    byte_num = int(re.match(r'(\d+)subr_page:(.+)', recv).group(1))
                    full_recv = recv
                    # recieve byte_num over buffer
                    if byte_num > 4096:
                        while len(full_recv) < byte_num:
                            recv = sock.recv(BUFF).decode()
                            full_recv += recv
                    subr_content = re.match(r'(\d+)subr_page:(.+)', full_recv).group(2)
                    self.display_subr(subr_content)

                elif re.match(r'(\d+)discussion:(.+)', recv):
                    # post and comments

                    byte_num = int(re.match(r'(\d+)discussion:(.+)', recv).group(1))
                    full_recv = recv
                    # recieve byte_num over buffer
                    if byte_num > 4096:
                        while len(full_recv) < byte_num:
                            recv = sock.recv(BUFF).decode()
                            full_recv += recv
                    content = re.match(r'(\d+)discussion:(.+)', full_recv).group(2)
                    comments = content.split(';')
                    main_post = eval(comments.pop(0))
                    self.view_discussion(main_post, comments)

                elif re.match(r'sure about subr:(.+)', recv):
                    # similar subreddit alert
                    subr_name = re.match(r'sure about subr:(.+)', recv).group(1)
                    self.subr_alert(subr_name)

                elif re.match(r'admin:subrs:users;(.+)', recv):
                    # number of users in all subreddit
                    subrs_info = re.match(r'admin:subrs:users;(.+)', recv).group(1)
                    subrs_info = subrs_info.split(';')
                    for i, subr in enumerate(subrs_info):
                        subr = subr.split(':')
                        subrs_info[i] = (subr[0], int(subr[1]))

                    self.sort_by_user_amount(subrs_info)

                elif re.match(r'admin:subrs:date;(.+)', recv):
                    # number of users in all subreddit
                    subrs_info = re.match(r'admin:subrs:date;(.+)', recv).group(1)
                    subrs_info = subrs_info.split(';')
                    for i, subr in enumerate(subrs_info):
                        subr = subr.split(':')
                        subrs_info[i] = (subr[0], subr[1])
                    
                    self.sort_by_date(subrs_info)
                
                elif re.match(r'admin:subrs:keyword;(.+)', recv):
                    # subreddits by keyword
                    subrs_info = re.match(r'admin:subrs:keyword;(.+)', recv).group(1)
                    subrs_info = subrs_info.split(';')
                    for i, subr in enumerate(subrs_info):
                        subr = subr.split(':')
                        subrs_info[i] = (subr[0], float(subr[1]))
                    
                    self.sort_by_keyword(subrs_info)

                elif re.match(r'(\d+)admin:subr_page:(.+)', recv):
                    # admin subreddit page
                    byte_num = int(re.match(r'(\d+)admin:subr_page:(.+)', recv).group(1))
                    full_recv = recv
                    # recieve byte_num over buffer
                    if byte_num > 4096:
                        while len(full_recv) < byte_num:
                            recv = sock.recv(BUFF).decode()
                            full_recv += recv
                    subr_content = re.match(r'(\d+)admin:subr_page:(.+)', full_recv).group(2)
                    self.admin_subr_info(subr_content)

                elif recv == 'banned':
                    self.banned()

                elif recv == 'banned_user':
                    self.banned_user()

                elif re.match(r'warning:(.+)', recv):
                    # user warning from admin
                    self.show_warning(re.match(r'warning:(.+)', recv).group(1))
                
                elif re.match(r'admin:subr:keywords(.+)', recv):
                    # keywords of subreddit
                    if re.match(r'admin:subr:keywords;(.+)', recv):
                        keywords = re.match(r'admin:subr:keywords;(.+)', recv).group(1)
                        keywords = keywords.split(';')
                        for i, word in enumerate(keywords):
                            word = word.split(':')
                            keywords[i] = (word[0], float(word[1]))

                        self.show_subr_keywords(keywords)
                    else:
                        self.data_List.delete(0, END)

                elif re.match(r'subr:users:(.+)', recv):
                    # users in a specific subreddit
                    users = eval(re.match(r'subr:users:(.+)', recv).group(1))
                    self.show_subr_users(users)

                elif re.match(r'admin:active_users;(.+)', recv):
                    # all users in different subreddits
                    self.show_active_users(re.match(r'admin:active_users;(.+)', recv).group(1))

                elif recv == 'profanity_detected':
                    # profanity alert
                    self.show_warning('profane language is not allowed')

                elif re.match(r'current_settings:(.+):(.+):(.+)', recv):
                    # show admin current settings
                    m_obj = re.match(r'current_settings:(.+):(.+):(.+)', recv)
                    self.show_current_settings(m_obj.group(1), m_obj.group(2), m_obj.group(3))

                elif recv == 'subr_created' or recv == 'post_created':
                    # return to home page after creating post or subreddit
                    self.logged_in()
                
                elif recv == 'community name already in use':
                    # alert when creating community
                    self.warning_lable['text'] = recv

            except ConnectionResetError:
                # in case server quits while connected
                print('server down')
                break

            except UnicodeDecodeError:
                # subreddit search result
                recv = pickle.loads(recv)
                self.in_home_page()
                self.show_subr_results(recv)
        sock.close()


if __name__ == '__main__':
    BUFF = 4096
    
    address = '172.18.64.1'
    sock = socket(AF_INET, SOCK_STREAM)
    # connect to server
    sock.connect((address, 11111))

    tk_class = tk_main()

    root = Tk()
    root.geometry('1500x800+100+100')
    root.minsize(300, 410)
    root.update()
    root.configure(background='white')

    style=ttk.Style()

    # set root ttk theme
    sv_ttk.set_theme("light")

    tk_class.main_tk()

    # start recieve thread
    thread = _thread.start_new_thread(tk_class.handler, ())

    root.mainloop()
