import praw
import threading
import time
import schedule
from tinydb import TinyDB, Query
import configparser


config = configparser.ConfigParser()
config.read('conf.ini')
client_id = config['REDDIT']['client_id']
client_secret = config['REDDIT']['client_secret']
reddit_user = config['REDDIT']['reddit_user']
reddit_pass = config['REDDIT']['reddit_pass']
target_subreddit = config['SETTINGS']['target_subreddit']
max_posts = config['SETTINGS']['max_posts']
reset_time = config['SETTINGS']['reset_time']

db = TinyDB('db.json')
db_query = Query()

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent='Daily submissions limiter (u/impshum)',
                     username=reddit_user,
                     password=reddit_pass)


def purge_db():
    db.purge()
    print('db purged')


def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


def printer(count, author, delete):
    if delete:
        print(f'DELETED: {author}')
    else:
        print(f'{count}: {author}')


def stream():
    print("""
██████╗ ███████╗██╗
██╔══██╗██╔════╝██║
██║  ██║███████╗██║
██║  ██║╚════██║██║
██████╔╝███████║███████╗
╚═════╝ ╚══════╝╚══════╝ v1.0

Daily Submissions Limiter (u/impshum)""")
    print(f'\nStreaming r/{target_subreddit}\n')
    now = time.time()
    for submission in reddit.subreddit(target_subreddit).stream.submissions():
        if submission.created_utc > now:
            id = submission.id
            author = submission.author.name
            query = db.get(db_query.author == author)
            if query:
                count = query['count']
                if count == int(max_posts):
                    printer(False, author, 1)
                    submission = reddit.submission(id)
                    submission.delete()
                else:
                    db.update({'count': count + 1}, db_query.author == author)
                    printer(count + 1, author, 0)
            else:
                db.insert({'author': author, 'count': 1})
                printer(1, author, 0)


def main():
    schedule.every().day.at(reset_time).do(run_threaded, purge_db)
    download_thread = threading.Thread(target=stream)
    download_thread.start()
    while 1:
        schedule.run_pending()
    time.sleep(1)


if __name__ == '__main__':
    main()
