from kivydialog.twine.twinedialog import TwineDialog

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import DictProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView


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
    current_name_override = StringProperty()

    # the widgets displaying the current name and text
    current_name_widget = ObjectProperty()
    current_text_widget = ObjectProperty()
    current_choices = None

    # the current dialog node the conversation is on
    current_node = ObjectProperty()

    # the current piece of text in the dialog node
    current_text_index = 0

    # used to replace {variables} with words
    word_overrides = DictProperty()  # variables -> replacements

    # the conversation id
    conversation_id = StringProperty()

    # the dialog object to use when querying the next piece of the conversation
    dialog = ObjectProperty()

    def __init__(self, **kwargs):
        super(Conversation, self).__init__(**kwargs)

        self.dialog = TwineDialog('/Users/horenstc/Development/Section8/assets/dialog.json')

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

        self.current_text_index = 0
        self.current_node = self.dialog.next(conversation_id)
        self.update_nodes()

    def update_nodes(self):
        """Refresh the list of current nodes. This function is also responsible
        for ensuring that either the dialog choices widget or the text widget
        is added to the Conversation layout.
        """
        if not self.current_node:
            self.current_node = self.dialog.next(self.conversation_id)

        if self.current_text_index == len(self.current_node.text):
            # user has hit end of text, display choices if any
            self.remove_widget(self.current_name_widget)
            self.remove_widget(self.current_text_widget)

            # if there are current choices, we're going to refresh them
            if self.current_choices:
                self.remove_widget(self.current_choices)
                self.current_choices = None

            # if there are choices available, display them, otherwise loop the conversation
            if self.current_node.choices:
                Logger.debug('Conversation: Displaying choices')
                self.current_choices = DialogChoices()

                for choice_id, choice_text in self.current_node.choices.iteritems():
                    button = Button(text=choice_text)
                    button.id = choice_id
                    button.bind(on_press=lambda instance: self.button_pressed(instance))
                    self.current_choices.add_widget(button)

                self.add_widget(self.current_choices)
            else:
                self.dispatch('on_complete')
                self.current_node = self.dialog.next(self.conversation_id)
                self.current_text_index = 0
                self.update_nodes()
        else:
            # we're displaying text, remove the current choices if any
            if self.current_choices:
                self.remove_widget(self.current_choices)
                self.current_choices = None

            # add the normal widgets back if necessary
            if not self.current_text_widget.parent:
                self.add_widget(self.current_name_widget)
                self.add_widget(self.current_text_widget)

            self.current_text_widget.text = self.current_node.text[self.current_text_index]

    def next(self):
        self.current_text_index += 1
        self.update_nodes()

    def on_touch_down(self, touch):
        # check if the touch happened on the dialog
        if self.collide_point(*touch.pos):
            if self.current_text_index < len(self.current_node.text):
                self.next()

        return super(Conversation, self).on_touch_down(touch)

    def button_pressed(self, instance):
        Logger.debug('Conversation: Button pressed')

        for choice_id, choice_text in self.current_node.choices.iteritems():
            if not choice_id == instance.id:
                continue

            self.current_node = self.dialog.next(choice_id)
            self.current_text_index = 0
        self.update_nodes()

    def _format_text(self, text):
        # use word overrides to replace variables in conversation text
        for variable, word in self.word_overrides.iteritems():
            text = text.replace('{' + variable + '}', word)

        return text

    def end_conversation(self):
        if isinstance(self.parent.parent, ConversationContainer):
            Logger.debug('Conversation: Calling ModalView dismiss()')
            self.parent.parent.dismiss(force=True)

        # notify any listeners that the conversation is over
        self.dispatch('on_complete')


class ConversationContainer(ModalView):
    conversation_id = StringProperty()

    conversation = ObjectProperty()

    def __init__(self, chat_map_file_path='', conversation_id=0, **kwargs):
        super(ConversationContainer, self).__init__(**kwargs)
        self.conversation_id = conversation_id

        Clock.schedule_once(lambda dt: self.conversation.change_conversation(self.conversation_id))
