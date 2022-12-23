import requests
from bs4 import BeautifulSoup
import os
from datetime import date
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tabulate import tabulate
#from dotenv import load_dotenv

# Check if "concurso" is eligible (i.e. is "Concurso" of "Enfermeiro")
def is_eligible(post):
    return set(["Concurso", "Enfermeiro"]) <= set(map((lambda a : a.text),post.find("span", {"class": "tags-links"}).find_all("a")))

# Notify of open "concursos" via email
def send_email(posts):
    
    #ENV_FROM = os.getenv('FROM')
    #ENV_PASSWORD = os.getenv('PASSWORD')
    #ENV_TO = os.getenv('TO')
    ENV_FROM = os.environ('FROM')
    ENV_PASSWORD = os.environ('PASSWORD')
    ENV_TO = os.environ('TO')
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Novos Concursos de Enfermagem | " + str(date.today().strftime("%d-%m-%Y"))
    message["From"] = ENV_FROM
    message["To"] = ENV_TO
    
    table_style = """
    <style>
    .gmail-table {
        border: solid 2px #DDEEEE;
        border-collapse: collapse;
        border-spacing: 0;
        font: normal 14px Roboto, sans-serif;
    }

    .gmail-table thead th {
        background-color: #DDEFEF;
        border: solid 1px #DDEEEE;
        color: #336B6B;
        padding: 10px;
        text-align: left;
        text-shadow: 1px 1px 1px #fff;
    }

    .gmail-table tbody td {
        border: solid 1px #DDEEEE;
        color: #333;
        padding: 10px;
        text-shadow: 1px 1px 1px #fff;
    }
    </style>
    """
    
    posts_table= []
    for id in posts:
       posts_table.append([posts[id]["title"],posts[id]["href"]])
    posts_html_table = tabulate(posts_table, headers=["Concurso", "Link"],tablefmt='html')\
        .replace("<table>",'''<table class="gmail-table">''')

    html = f"""
        <html>
        <head>
        {table_style}
        </head>
        <body>
            <p>Olá,<br>
            Aqui estão os concursos que abriram hoje:<br>
            </p>
        {posts_html_table}
        </body>
        </html>
        """

    message.attach(MIMEText(html, "html"))
    
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    port = 465  # For SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(ENV_FROM, ENV_PASSWORD)
        server.sendmail(ENV_FROM, ENV_TO.split(","), message.as_string())


### MAIN ###
#load_dotenv()

# Get page HTML
URL = "http://www.aenfermagemeasleis.pt/"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

# Considered posts
posts_dict = {}

# Open file of "concursos" already processed
#ENV_STORAGE_FILE_PATH = os.getenv('STORAGE_FILE_PATH')
ENV_STORAGE_FILE_PATH = os.environ('STORAGE_FILE_PATH')
file = open(ENV_STORAGE_FILE_PATH + "/concursos.txt", "r+")
posts_already_processed = file.read()

for post in soup.find_all("article"):
    
    post_id = post.get("id")
    
    # Check if post is eligible or was already processed
    if (not is_eligible(post) or post_id in posts_already_processed):
        continue

    post_title = post.find("h1").text
    post_href = post.find("a").get("href")
    
    posts_dict[post_id] = { "title" : post_title, "href" : post_href}

# Notify
if len(posts_dict) > 0:
    send_email(posts_dict)
    file.write("\n".join(list(posts_dict.keys())) + "\n")

file.close()