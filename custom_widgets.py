import urwid

class MyButton(urwid.Button):
    '''
    - override __init__ to use our ButtonLabel instead of urwid.SelectableIcon

    - make button_left and button_right plain strings and variable width -
      any string, including an empty string, can be set and displayed

    - otherwise, we leave Button behaviour unchanged
    '''
    button_left = ""
    button_right = ""

    def __init__(self, c, on_press=None, user_data=None):
        self._label = ButtonLabel("")

        self.secret_id = c['id']
        self.secret_name = c['id'].rsplit('/', 1)[-1] # get the secret name from the url
        self.secret_value = ""

        cols = urwid.Columns([
            ('fixed', len(self.button_left), urwid.Text(self.button_left)),
            self._label,
            ('fixed', len(self.button_right), urwid.Text(self.button_right))],
            dividechars=1)
        super(urwid.Button, self).__init__(cols)

        
        if on_press:
            urwid.connect_signal(self, 'click', on_press, user_data)

        self.set_label(self.secret_name)


class ButtonLabel(urwid.SelectableIcon):
    '''
    use Drunken Master's trick to move the cursor out of view
    '''
    def set_text(self, label):
        '''
        set_text is invoked by Button.set_label
        '''
        self.__super.set_text(label)
        self._cursor_position = len(label) + 1


class ListEntry(urwid.Text):
    _selectable = True

    signals = ["click"]

    def __init__(self, c, layout=None):



        self.secret_id = c['id']
        self.secret_name = c['id'].rsplit('/', 1)[-1] # get the secret name from the url
        self.secret_value = ""

        markup = self.secret_name
        self.__super.__init__(markup)
        self._cache_maxcol = None

    def keypress(self, size, key):
        """
        Send 'click' signal on 'activate' command.
        """
        if self._command_map[key] != urwid.ACTIVATE:
            return key

        self._emit('click')

    def mouse_event(self, size, event, button, x, y, focus):
        """
        Send 'click' signal on button 1 press.
        """
        if button != 1 or not urwid.util.is_mouse_press(event):
            return False

        self._emit('click')
        return True