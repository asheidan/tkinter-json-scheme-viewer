#!/usr/bin/env python3

from collections.abc import Sequence
from tkinter import ttk
import tkinter as tk
import tkinter.font as tk_font
from typing import Optional

STRUCTURE = [
    ("Representation", "", [
        ("id", "string<uuid>"),
        ("apa", "integer"),
        ("bepa", "list<string>"),
        ("some_list", "list<Foo>", [
            ("id", "integer"),
        ]),
    ])
]


def append_to(tree, parent: str = "", text: Optional[str] = None, tags: Sequence = (), values: Sequence = ()) -> str:
    return tree.insert(parent=parent, index="end", text=text, values=values, tags=tags, open=True)


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master=master)

        self.default_font = tk_font.nametofont("TkDefaultFont")
        self.default_font.configure(size=-11)
        #tk_font.nametofont("TkBoldFont").configure(size=-11)

        #self.grid()
        self.pack(fill='both')

        self.create_widgets()
        self.bind_keys()

    def create_widgets(self):
        style = ttk.Style(self)

        #print(style.theme_names())
        #style.theme_use('alt')

        style.configure('Treeview', rowheight=17)
        style.configure('Treeview.Heading', font=self.default_font)

        # print(tk_font.families())
        #mono_font = tk_font.Font( #family="Fira Code", size=-11,)
        font_bold = tk_font.Font(weight='bold', size=-11)

        self.tree_view = ttk.Treeview(self, columns=("Type",), height=50, selectmode="browse", displaycolumns=('Type',))  # , show="tree")
        self.tree_view.tag_configure('parent', font=font_bold)

        #self.tree_view.heading('Name', text='Name')
        self.tree_view.heading('Type', text='Type')

        self.tree_view.column(0, stretch=True)

        #self.tree_view.grid()
        self.tree_view.pack(fill='both')

        self.parse_structure(structure=STRUCTURE)

    def parse_structure(self, structure, parent=""):
        for name, type_description, *children in structure:
            current = append_to(self.tree_view, parent=parent, text=name, values=(type_description,), tags=('parent',) if children else ())
            if children:
                self.parse_structure(parent=current, structure=children[0])

    def toggle_type_column(self, event: tk.Event):
        widget = event.widget

        # This should only be a widget with columns
        display_columns = widget["displaycolumns"]

        match display_columns:
            case ('#all',):
                widget["displaycolumns"] = []
            case '':
                widget["displaycolumns"] = ('Type',)
                widget.column('Type', width=int(widget.winfo_width()/(len(widget["displaycolumns"])+1)))
            case other:
                if 'Type' in other:
                    widget["displaycolumns"] = tuple(c for c in other if c != 'Type')
                else:
                    widget["displaycolumns"] = other + ('Type',)



    def bind_keys(self):
        self.tree_view.bind('<KeyPress-j>', lambda event: event.widget.event_generate('<Down>', when='tail'))
        self.tree_view.bind('<KeyPress-k>', lambda event: event.widget.event_generate('<Up>', when='tail'))
        self.tree_view.bind('<KeyPress-h>', lambda event: event.widget.event_generate('<Left>', when='tail'))
        self.tree_view.bind('<KeyPress-l>', lambda event: event.widget.event_generate('<Right>', when='tail'))

        self.tree_view.bind('<KeyPress-T>', self.toggle_type_column)



def main() -> None:
    #root: tk.Tk = tk.Tk()
    #root.mainloop()

    app = Application()
    app.master.title("Foo")

    app.mainloop()


if __name__ == "__main__":
    main()
