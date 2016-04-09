import sys
import urllib
import urllib2
import httplib2
import json


class Issue:
    def __init__(self, card, type = None):
        self._name = card['name'].encode("utf-8")
        self._description = card['desc'].encode("utf-8")
        self._type = 'Epic'

    @property
    def get_name(self):
        return self._name

    @property
    def get_description(self):
        return self._description

    @property
    def get_type(self):
        return self._type

    def __str__(self):
        return '(Name): {0}, (description): {1}, (type): {2}, (priority): {3}'.format(self._name,
                                                                              self._description,
                                                                              self._type)


def login(username, password, instance_name):
    login_date = urllib.urlencode({'login': username, 'password': password})

    http_req = httplib2.Http()

    headers = {'Content-Length': str(len(login_date)), 'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': ''}

    response, content = http_req.request('http://{0}.myjetbrains.com/youtrack/rest'.format(instance_name) + "/user/login",
            'POST',
            headers= headers,
            body=login_date)
    return response['set-cookie']


def getboardID(key, token, board_name):

    request_URL = 'https://api.trello.com/1/members/me/boards?key={0}&token={1}'.format(key, token)
    JSON_RESPONSE = urllib2.urlopen(request_URL)
    boards = json.load(JSON_RESPONSE)

    for board in boards:
        if board_name == board['name']:
            return board['id']
    return None


def getlistID(key, token, board_ID,list_name):

    request_URL = 'https://api.trello.com/1/boards/{0}/lists?key={1}&token={2}'.format(board_ID, key, token)
    JSON_RESPONSE = urllib2.urlopen(request_URL)
    lists = json.load(JSON_RESPONSE)

    for list in lists:
        if list['name'] == list_name:
            return list['id']

    return None


#lists can be board name or list name
def getCards(key, token, list_name, board_ID):

    if list_name == 'all':
        request_URL = 'https://api.trello.com/1/boards/{0}/cards?fields=name,desc,labels&key={1}&' \
                      'token={2}'.format(board_ID, key, token)
    else:
        list_ID = getlistID(key, token, board_ID, list_name)

        #Couldn't get LIST_ID
        if list_ID == None:
            return None

        request_URL = 'https://api.trello.com/1/lists/{0}/cards?fields=name,desc,labels&key={1}&token={2}'.format(list_ID,
                                                                                                                  key,token)

    JSON_RESPONSE = urllib2.urlopen(request_URL)
    cards = json.load(JSON_RESPONSE)

    return cards


def getIssuesArray(cards):

    issues_array = []

    for card in cards:
        new_issue = Issue(card)
        issues_array.append(new_issue)

    return issues_array


def ImportToYoutrack(username, password, youtrack_instance_name, project_id, issues_array, cookie):

    youtrack_baseurl = 'http://{0}.myjetbrains.com/youtrack/rest/issue'.format(youtrack_instance_name)

    http_req2 = httplib2.Http()

    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': cookie}

    for issue in issues_array:
        data = urllib.urlencode({'project': project_id, 'summary': issue.get_name, 'description': issue.get_description,
                                'type': issue.get_type})
        headers['Content-Length']= str(len(data))

        response, content = http_req2.request(youtrack_baseurl.encode('utf-8'), 'PUT', headers = headers, body=data)


def main():
    if len(sys.argv) != 9:
        print 'inappropriate number of arguments.. closing'
        return

    key = sys.argv[1]
    token = sys.argv[2]
    board_name = sys.argv[3]
    list_name = sys.argv[4]
    instance_name = sys.argv[5]
    project_ID = sys.argv[6]
    username = sys.argv[7]
    password = sys.argv[8]

    print 'Loggin to Youtrack...'
    cookie = login(username, password, instance_name)

    print 'Getting Trello data...'
    board_ID = getboardID(key, token, board_name)

    #Couldn't get board_ID
    if board_ID == None:
        print 'Wrong board name: {0}'.format(board_name)
        return

    cards = getCards(key, token, list_name, board_ID)

    #Couldn't get list_ID due to wrong list name
    if cards == None:
        print 'Wrong list name: {0}'.format(list_name)
        return

    issues = getIssuesArray(cards)

    print 'Making Youtrack issues....'
    ImportToYoutrack(username, password, instance_name, project_ID, issues, cookie)

    print 'Done importing to youtrack :)'

from TtY.Migration import Migration


def new_main():
    with Migration("mapping.json", "specs.json") as test_string:
        print test_string

if __name__ == "__main__":
    new_main()
