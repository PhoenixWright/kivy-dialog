from kivy.app import App
from conversation import ConversationContainer

class DialogApp(App):
    def build(self):
        return ConversationContainer('chatmap.json', 1)


if __name__ == '__main__':
    DialogApp().run()
