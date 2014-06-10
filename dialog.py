import yaml
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import DictProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView

from chatmap import ChatMap


class CutsceneText(ModalView):
    current_text = StringProperty()
    text_list = ListProperty()

    # automatically progress through the text
    text_timer = NumericProperty(3.0)

    def __init__(self, text_list=None, **kwargs):
        """
        :param text_list: A list of strings to show one after the other.
        :type text_list: list[str]
        """
        super(CutsceneText, self).__init__(**kwargs)
        self.register_event_type('on_complete')

        if text_list:
            self.text_list.extend(text_list)
        self.current_text = self.text_list.pop(0)
        Clock.schedule_once(self.next_text, self.text_timer)

    def on_complete(self):
        pass

    def next_text(self, *args):
        if self.text_list:
            self.current_text = self.text_list.pop(0)
            Clock.schedule_once(self.next_text, self.text_timer)
        else:
            self.dispatch('on_complete')
            self.dismiss()

    def on_touch_down(self, touch):
        pass


class DialogChoices(BoxLayout):

    def __init__(self, **kwargs):
        super(DialogChoices, self).__init__(**kwargs)
        self.orientation = 'vertical'


class Conversation(BoxLayout):
    current_name = StringProperty()
    current_text = StringProperty()
    current_name_override = StringProperty(None)

    # the widgets displaying the current name and text
    current_name_widget = ObjectProperty()
    current_text_widget = ObjectProperty()

    current_choices = None

    # normal 'list of text' conversation
    conversations = ObjectProperty()

    # chat_mapper variables
    chat_map = ObjectProperty()
    current_nodes = []
    current_node_id = 0

    # used to replace {variables} with words
    word_overrides = DictProperty()  # variables -> replacements

    # intializers
    conversation_id = ObjectProperty()

    def __init__(self, **kwargs):
        super(Conversation, self).__init__(**kwargs)

        with open('assets/conversations.yaml') as f:
            loaded_yaml = yaml.load(f.read())
            self.conversations = loaded_yaml['conversations']

        # load the chat map
        self.chat_map = ChatMap('assets/chatmap.json')

        self.current_dialog_node_id = 0

        self.register_event_type('on_complete')

    def on_complete(self):
        pass

    def change_conversation(self, conversation_id, word_overrides=None):
        """Change to a different conversation.
        :param conversation_id: The conversation id to switch to.
        :type conversation_id: int
        :param word_overrides: A dictionary of variable names to words.
        :type word_overrides: dict
        """
        self.conversation_id = conversation_id

        if word_overrides:
            # replace the current overrides with new ones
            self.word_overrides.clear()
            self.word_overrides.update(word_overrides)

        self.current_dialog_node_id = 0
        self.update_nodes()

    def update_nodes(self):
        """Refresh the list of current nodes. This function is also responsible
        for ensuring that either the dialog choices widget or the text widget
        is added to the Conversation layout.
        """
        # find out if we're using chatmapper for this convo
        chat_mapper = isinstance(self.conversation_id, int)

        # clear the current_nodes list
        self.current_nodes = []

        if chat_mapper:
            current_node = self.chat_map.conversations[self.conversation_id].dialog_nodes[self.current_node_id]
        else:
            current_node = self.conversations[self.conversation_id][self.current_node_id]

        if chat_mapper and current_node.is_root:
            Logger.debug('Conversation: Hit root node. Moving to next node')
            self.current_node_id += 1
            self.update_nodes()
        elif chat_mapper and current_node.is_group:
            self.remove_widget(self.current_name_widget)
            self.remove_widget(self.current_text_widget)

            # if there are current choices, we're going to refresh them
            if self.current_choices:
                self.remove_widget(self.current_choices)
                self.current_choices = None
            Logger.debug('Conversation: Hit group node')

            # collect the outgoing links
            for link in current_node.outgoing_links:
                convo = self.chat_map.conversations[link.destination_convo_id]
                self.current_nodes.append(convo.dialog_nodes[link.destination_dialog_id])

            Logger.debug('Conversation: Collected {} nodes in the group'.format(len(self.current_nodes)))

            self.current_choices = DialogChoices()

            for node in self.current_nodes:
                if node.is_group:
                    button_text = node.title
                else:
                    button_text = node.menu_text
                button = Button(text=button_text)
                button.id = str(node.id)
                button.bind(on_press=lambda instance: self.button_pressed(instance))
                self.current_choices.add_widget(button)

            self.add_widget(self.current_choices)
        else:
            # it's a regular node
            if self.current_choices:
                self.remove_widget(self.current_choices)
                self.current_choices = None

            if not self.current_text_widget.parent:
                # add the normal widgets back
                self.add_widget(self.current_name_widget)
                self.add_widget(self.current_text_widget)

            self.current_nodes.append(current_node)

            # apply a name override if specified
            if chat_mapper:
                self.current_name = self.chat_map.actors[current_node.actor].name
                self.current_text_widget.text = self._format_text(current_node.dialogue_text)
            else:
                # set the current name to whatever is in the conversation node
                # name attr if it exists
                self.current_name = getattr(current_node, 'name', '')
                if hasattr(current_node, 'text'):
                    self.current_text_widget.text = current_node.text
                else:
                    self.current_text_widget.text = current_node

    def next(self):
        # find out if we're using chatmapper for this convo
        chat_mapper = isinstance(self.conversation_id, int)

        if chat_mapper:
            current_node = self.chat_map.conversations[self.conversation_id].dialog_nodes[self.current_node_id]
            if len(current_node.outgoing_links) == 0:
                Logger.debug('Conversation: No more outgoing links. Conversation over')
                self.end_conversation()
            else:
                destination_dialog_id = current_node.outgoing_links[0].destination_dialog_id
                new_node = self.chat_map.conversations[self.conversation_id].dialog_nodes[destination_dialog_id]

                # check if the new node is just a blank button
                if hasattr(new_node, 'dialogue_text') and not new_node.dialogue_text and not new_node.is_group:
                    Logger.debug('Conversation: New node is just a blank button, moving to next node')
                    self.current_node_id = new_node.outgoing_links[0].destination_dialog_id
                else:
                    # update the current node id
                    self.current_node_id = destination_dialog_id
                self.update_nodes()
        else:
            self.current_node_id += 1
            if self.current_node_id == len(self.conversations[self.conversation_id]):
                Logger.debug('Conversation: Hit end of conversation, ending...')
                self.end_conversation()
            else:
                self.update_nodes()

    def on_touch_down(self, touch):
        # check if the touch happened on the dialog
        if self.collide_point(*touch.pos):
            if len(self.current_nodes) == 1:
                self.next()

        return super(Conversation, self).on_touch_down(touch)

    def button_pressed(self, instance):
        Logger.debug('Conversation: Button pressed')
        for node in self.current_nodes:
            if not str(node.id) == instance.id:
                continue

            if node.is_group:
                Logger.debug('Conversation: Clicked node is a group, displaying options')
                self.current_node_id = node.id
            elif node.dialogue_text:
                Logger.debug('Conversation: Clicked button has dialogue text. Setting to current node')
                self.current_node_id = node.id
            else:
                Logger.debug('Conversation: Moving to button\'s outgoing link')
                if len(node.outgoing_links) == 0:
                    Logger.debug('Conversation: No more outgoing links. Conversation over')
                    self.end_conversation()
                    return
                self.current_node_id = node.outgoing_links[0].destination_dialog_id

            self.update_nodes()
            return

    def _format_text(self, text):
        # use word overrides to replace variables in conversation text
        for variable, word in self.word_overrides.iteritems():
            text = text.replace('{' + variable + '}', word)

        # TODO: make this take multiple clicks to progress through
        text = text.replace('|', '\n')

        return text

    def end_conversation(self):
        if isinstance(self.parent.parent, ConversationContainer):
            Logger.debug('Conversation: Calling ModalView dismiss()')
            self.parent.parent.dismiss(force=True)

        # notify any listeners that the conversation is over
        self.dispatch('on_complete')


class ConversationContainer(ModalView):
    chat_map_file_path = StringProperty()
    conversation_id = ObjectProperty()

    conversation = ObjectProperty()

    def __init__(self, chat_map_file_path='', conversation_id=0, **kwargs):
        super(ConversationContainer, self).__init__(**kwargs)
        self.chat_map_file_path = chat_map_file_path
        self.conversation_id = conversation_id

        Clock.schedule_once(lambda dt: self.conversation.change_conversation(self.conversation_id))
