# coding=UTf-8
from datetime import datetime
import requests
import json
import base64


class YouTrack:
    def __init__(self, trello_key, trello_token, youtrack_login, youtrack_password, youtrack_link, youtrack_project, youtrack_subsystem=None):
        self.trello_key = trello_key
        self.trello_token = trello_token
        self.youtrack_login = youtrack_login
        self.youtrack_password = youtrack_password
        self.youtrack_link = youtrack_link
        self.youtrack_project = youtrack_project
        self.youtrack_subsystem = youtrack_subsystem

    def import_issues(self, trello_cards, mapping_dict, number_in_project, attachments=False, comments=False):
        for card in trello_cards:
            attachmentsArray = {}
            commentsArray = []

            if attachments:
                for attachment in card["attachments"]:
                    if attachment["isUpload"]:
                        headers = {'Authorization': 'OAuth oauth_consumer_key="%s", oauth_token="%s"' % (self.trello_key, self.trello_token)}
                        response = requests.get(attachment["url"], headers=headers)
                        filePath = 'files/' + attachment['name']
                        file = open(filePath, 'wb')
                        file.write(response.content)
                        file.close()
                        attachmentsArray[attachment["name"]] = filePath
                    else:
                        card["desc"] += "\n" + attachment["url"]

            if comments:
                commentsArray = [{"text": comment["text"], "usesMarkdown": True} for comment in card["comments"]]

            json_string = json.dumps({
                "summary": card["name"],
                "description": card["desc"],
                "usesMarkdown": True,
                "comments": commentsArray,
            })

            import_url = '%s/api/admin/projects/%s/issues?fields=id,idReadable&muteUpdateNotifications=true' % (self.youtrack_link, self.youtrack_project)
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer',
            }
            response = requests.post(import_url, auth=(self.youtrack_login, self.youtrack_password),
                                    headers=headers, data=json_string.encode('utf-8'))
            print(response.content)

            issue = response.json()
            attachmentUrl = '%s/api/issues/%s/attachments?fields=id,name' % (self.youtrack_link, issue["id"])
            headers = {
                'Authorization': 'Bearer',
            }
            for name in attachmentsArray:
                with open(attachmentsArray[name], 'rb') as file:
                    response = requests.post(attachmentUrl, auth=(self.youtrack_login, self.youtrack_password), headers=headers, files={name: file})
                    print(response.content)

        print('√ Done Importing cards to Youtrack')

    def import_users(self, trello_users):
        xml_string = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        xml_string += '<list>\n'
        xml_string += '\n'.join(['<user login="%s" fullName="%s" email="%s"/>'
                                 % (user["username"], user["fullName"], "None" if not user["email"] else user["email"])
                                 for user in trello_users])
        xml_string += '</list>\n'

        headers = {'Content-Type': 'application/xml'}
        response = requests.put(self.youtrack_link + "/rest/import/users", data=xml_string.decode('utf-8'),
                                headers=headers, auth=(self.youtrack_login, self.youtrack_password))

    @staticmethod
    def _time_now():
        return str(int(datetime.now().strftime("%s")) * 1000)
