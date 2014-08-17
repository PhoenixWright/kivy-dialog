import re
import simplejson as json

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convert(name):
    # eliminate spaces
    name = name.replace(' ', '')

    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def field_init(self, field_dict):
    """Inits a class where there are only fields to worry about."""
    for item in field_dict:
        setattr(self, convert(item), field_dict[item])


Actor = type('Actor', (), {'__init__': field_init})
Item = type('Item', (), {'__init__': field_init})
Location = type('Location', (), {'__init__': field_init})
OutgoingLink = type('OutgoingLink', (), {'__init__': field_init})
UserVariable = type('UserVariable', (), {'__init__': field_init})


class DialogNode:
    def __init__(self, dn_json):
        self.outgoing_links = list()
        for item in dn_json:
            if item == 'OutgoingLinks':
                for item2 in dn_json['OutgoingLinks']:
                    self.outgoing_links.append(OutgoingLink(item2))
            elif item == 'Fields':
                for item2 in dn_json['Fields']:
                    value = dn_json['Fields'][item2]

                    # some of the chatmapper ids are in string form
                    # change them to ints
                    if value.isdigit():
                        value = int(value)
                    setattr(self, convert(item2), value)
            else:
                setattr(self, convert(item), dn_json[item])


class Conversation:
    def __init__(self, conv_json):
        self.dialog_nodes = dict()
        for item in conv_json['DialogNodes']:
            self.dialog_nodes[item['ID']] = DialogNode(item)

        self.node_color = conv_json['NodeColor']


class ChatMap:
    def __init__(self, filepath):
        fp = open(filepath)
        chatmap = json.loads(fp.read())
        fp.close()

        self.title = chatmap['Title']
        self.version = chatmap['Version']
        self.author = chatmap['Author']
        self.description = chatmap['Description']
        self.user_script = chatmap['UserScript']

        self.actors = dict()
        for item in chatmap['Assets']['Actors']:
            self.actors[item['ID']] = Actor(item['Fields'])

        self.items = dict()
        for item in chatmap['Assets']['Items']:
            self.items[item['ID']] = Item(item['Fields'])

        self.locations = dict()
        for item in chatmap['Assets']['Locations']:
            self.locations[item['ID']] = Location(item['Fields'])

        self.conversations = dict()
        for item in chatmap['Assets']['Conversations']:
            self.conversations[item['ID']] = Conversation(item)

        self.user_variables = dict()
        for item in chatmap['Assets']['UserVariables']:
            self.user_variables[item['ID']] = UserVariable(item)
