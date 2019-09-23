'''
Filename: run_query.py
Author(s): Joshua Kruse and Champ Foronda
Description: Script that runs a query on pull requests in a repository and writes them into a CSV file
'''
import requests
import json
import csv
import pymongo
from config import GITHUB_AUTHORIZATION_KEY

headers = {"Authorization": GITHUB_AUTHORIZATION_KEY}

def setup_query(owner = "", name = "", pull_request_number = 1, comment_range = 10):
  query = f'''
  query {{
  repository(owner: {owner}, name: {name}) {{
    pullRequest: issueOrPullRequest(number: {pull_request_number}) {{
      __typename
      ... on PullRequest {{
        title
        number
        closed
        author {{
            login 
        }}
        bodyText
        comments(first: {comment_range}) {{
          edges {{
            node {{
              author {{
                login
              }}
              bodyText
            }}
          }}
        }}
        reviewThreads(first: 100) {{
          edges {{
            node {{
              comments(first: {comment_range}) {{
                nodes {{
                  author {{
                    login
                  }}
                  bodyText
                  authorAssociation
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
  }}'''
  return query

# Funtion that uses requests.post to make the API call
def run_query(query):
  request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
  if request.status_code == 200:
      return request.json()
  else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

def get_comments_from_review_threads(query_data):
  review_nodes = query_data['data']['repository']['pullRequest']['reviewThreads']['edges']
  list_of_comments = dict()
  for review_node in review_nodes:
    for comment in review_node['node']['comments']['nodes']:
      list_of_comments.update({comment['author']['login'] : comment['bodyText']})

  return list_of_comments

def get_comments_from_pull_request(query_data):
  comment_edges = query_data['data']['repository']['pullRequest']['comments']['edges']
  list_of_comments = dict()
  for edge in comment_edges:
    list_of_comments.update({edge['node']['author']['login'] : edge['node']['bodyText']})

  return list_of_comments

def write_pull_request_comments_to_csv(list_of_comments=[]):
  with open('pull_request_comments.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file, delimiter=',')
    for comment in list_of_comments:
      writer.writerow([comment])
    csv_file.close()

def write_review_comments_to_csv(list_of_comments=[]):
  with open('review_thread_comments.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file, delimiter=',')
    for comment in list_of_comments:
      writer.writerow([comment])
    csv_file.close()


# Executes the query
query = setup_query("astropy", "astropy", 5, 10)
query_data = run_query(query)
list_of_pull_request_comments = get_comments_from_pull_request(query_data)
list_of_review_thread_comments = get_comments_from_review_threads(query_data)

# Adds comments to a MongoDB
client = pymongo.MongoClient("mongodb+srv://jek248:SentimentAnalysis@sentiment-analysis-8snlg.mongodb.net/test?retryWrites=true&w=majority")
db = client['testing_db']
db_collection = db['pull_request_comments']
db_collection.insert_one( list_of_pull_request_comments )
db_collection.insert_one( list_of_review_thread_comments )
client.close()

# Adds comments to a CVS file
#write_review_comments_to_csv(list_of_review_thread_comments)
#write_pull_request_comments_to_csv(list_of_pull_request_comments)

