import os
import sys
import json
import argparse
import urwid
import jmespath
import collections

from custom_widgets import MyButton


class kvDisplay():

    PALETTE = [
        ('input expr', 'black,bold', 'light gray'),
        ('bigtext', 'white', 'black'),
        ('highlight', 'white', 'dark gray')
    ]

    choices = [ u"test2", u"test4",  u"test5",
                u"test7", u"test8",  u"test9"
              ]

    def __init__(self, output_mode='result'):
        self.view = None
        self.output_mode = output_mode
        self.last_result = None
 
    def _get_font_instance(self):
        return urwid.get_all_fonts()[-2][1]()

    def handle_enter(self, c, other):
        self.secret_details.set_text(c + ' select worked!')

    def handle_scroll(self, listBox):
        index = listBox.focus_position
        #widget = listBox.body[index]
        self.secret_details.set_text("Index of selected item: " + str(index))

    def listbox_secrets(self, choices):
        body = [urwid.Divider()]
        for c in choices:
            button = MyButton(c)
            urwid.connect_signal(button, 'click', self.handle_enter, user_args = [c])
            body.append(urwid.AttrMap(button, None, focus_map = 'highlight'))

        walker = urwid.SimpleListWalker(body)
        listBox = urwid.ListBox(walker)
        
        # pass the whole listbox to the handler
        urwid.connect_signal(walker, "modified", self.handle_scroll, user_args = [listBox] )

        return listBox


    def _create_view(self):

        ### header
        self.input_expr = urwid.Edit(('input expr', 'Search secrets: '))

        sb = urwid.BigText('KV Client', self._get_font_instance())
        sb = urwid.Padding(sb, 'center', None)
        sb = urwid.AttrWrap(sb, 'bigtext')
        sb = urwid.Filler(sb, 'top', None, 5)
        self.status_bar = urwid.BoxAdapter(sb, 5)

        div = urwid.Divider()
        self.header = urwid.Pile([self.status_bar, div,
             urwid.AttrMap(self.input_expr, 'input expr'), div],
            focus_item=2)


        ### content

        self.left_content = self.listbox_secrets(self.choices)
        self.left_content = urwid.LineBox(self.left_content, title='Secret list')

        self.secret_details = urwid.Text("start_text")
        self.secret_details_list = [div, self.secret_details]

        self.right_content = urwid.ListBox(self.secret_details_list)
        self.right_content = urwid.LineBox(self.right_content, title='Secret details')

        self.content = urwid.Columns([('weight',1.5, self.left_content), self.right_content])
        
        ### footer
        self.footer = urwid.Text("Status: ")


        ### frame config
        self.view = urwid.Frame(body=self.content, header=self.header,
                                footer=self.footer, focus_part='content')



    def main(self, screen=None):
        self._create_view()
        self.loop = urwid.MainLoop(self.view, self.PALETTE,
                                   unhandled_input=self.unhandled_input,
                                   screen=screen)
        self.loop.screen.set_terminal_properties(colors=256)
        self.loop.run()


    def unhandled_input(self, key):
        if key == 'f5':
            raise urwid.ExitMainLoop()
        elif key == 'ctrl ]':
            # Keystroke to quickly empty out the
            # currently entered expression.  Avoids
            # having to hold backspace to delete
            # the current expression current expression.
            self.input_expr.edit_text = ''
            self.secret_details.set_text('')

            

def main():

    screen = urwid.raw_display.Screen()
    display = kvDisplay()
    display.main(screen=screen)


if __name__ == '__main__':
    sys.exit(main())