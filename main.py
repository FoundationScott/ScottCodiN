import tkinter as tk
from tkinter import filedialog, messagebox
import os
import keyword
import re
from typing import List, Tuple
import webbrowser

class CodeIDE:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("ScottCodiN IDE")
        self.master.geometry("800x600")
        
        self.filename = None
        self.current_language = None
        self.text_area = tk.Text(self.master, undo=True, wrap="none")
        self.text_area.pack(fill=tk.BOTH, expand=1)
        
        self.create_menu()
        self.create_scrollbars()
        self.bind_events()
        self.select_all_timer = None
    
    def create_menu(self):
        menu_bar = tk.Menu(self.master)
        
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_ide)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.text_area.edit_undo)
        edit_menu.add_command(label="Redo", command=self.text_area.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.edit_action('cut'))
        edit_menu.add_command(label="Copy", command=lambda: self.edit_action('copy'))
        edit_menu.add_command(label="Paste", command=lambda: self.edit_action('paste'))
        edit_menu.add_command(label="Delete", command=lambda: self.edit_action('delete'))
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="Full Guide", command=self.open_guide)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.master.config(menu=menu_bar)
    
    def create_scrollbars(self):
        self.scroll_y = tk.Scrollbar(self.master, orient=tk.VERTICAL, command=self.text_area.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=self.scroll_y.set)
        
        self.scroll_x = tk.Scrollbar(self.master, orient=tk.HORIZONTAL, command=self.text_area.xview)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_area.config(xscrollcommand=self.scroll_x.set)
    
    def bind_events(self):
        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.text_area.bind("<Return>", self.on_return)
        self.text_area.bind("<Configure>", self.update_scroll_region)
        self.text_area.bind("<Button-4>", self.scroll_up)
        self.text_area.bind("<Button-5>", self.scroll_down)
        self.text_area.bind("<ButtonPress-1>", self.start_select_all_timer)
        self.text_area.bind("<ButtonRelease-1>", self.stop_select_all_timer)
    
    def set_language(self):
        first_line = self.text_area.get("1.0", "2.0").strip()
        match = re.match(r"^\s*(#|\/\/)\s*--\+\+(\w+)\+\+--", first_line)
        if match:
            self.current_language = match.group(2).lower()
            self.highlight_syntax()
        else:
            self.current_language = None
            # Only show error if cursor is not on the first line
            cursor_position = self.text_area.index(tk.INSERT)
            if cursor_position.split('.')[0] != '1':
                self.show_error("First line must specify language, e.g., '# --++Python++--' or '// --++C#++--'")
    
    def on_key_release(self, event=None):
        cursor_position = self.text_area.index(tk.INSERT)
        if self.current_language is None and cursor_position.split('.')[0] != '1':
            self.set_language()
        self.highlight_syntax()
    
    def on_return(self, event):
        current_line = self.text_area.get("insert linestart", "insert")
        indent_match = re.match(r"^\s+", current_line)
        new_line_indent = indent_match.group(0) if indent_match else ""
        
        if current_line.rstrip().endswith((':', '{', '[', '(', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally')):
            new_line_indent += "    "
        
        self.text_area.insert("insert", "\n" + new_line_indent)
        return "break"
    
    def highlight_syntax(self):
        if self.current_language not in ["python", "csharp", "ruby", "cpp", "lua", "luau"]:
            return
        
        self.text_area.tag_remove("keyword", "1.0", tk.END)
        self.text_area.tag_remove("builtin", "1.0", tk.END)
        self.text_area.tag_remove("comment", "1.0", tk.END)
        self.text_area.tag_remove("string", "1.0", tk.END)
        
        content = self.text_area.get("1.0", tk.END)
        for pattern, tag in self.get_syntax_patterns():
            for match in re.finditer(pattern, content, re.MULTILINE):
                start, end = match.span()
                start_index = f"1.0 + {start} chars"
                end_index = f"1.0 + {end} chars"
                self.text_area.tag_add(tag, start_index, end_index)
    
    def get_syntax_patterns(self) -> List[Tuple[str, str]]:
        python_patterns = [
            (r"\b(" + "|".join(keyword.kwlist) + r")\b", "keyword"),
            (r"\b(__init__|self)\b", "builtin"),
            (r"#.*", "comment"),
            (r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", "string")
        ]
        
        csharp_patterns = [
            (r"\b(class|public|private|protected|internal|static|void|int|string|bool|new|return|namespace|using|if|else|for|while|foreach|in|break|continue|switch|case|default|do|try|catch|finally|throw)\b", "keyword"),
            (r"\b(Console|Math|String|Int32|Double|List|Dictionary)\b", "builtin"),
            (r"//.*", "comment"),
            (r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", "string")
        ]
        
        ruby_patterns = [
            (r"\b(alias|and|begin|break|case|class|def|defined|do|else|elsif|end|ensure|false|for|if|in|module|next|nil|not|or|redo|rescue|retry|return|self|super|then|true|undef|unless|until|when|while|yield)\b", "keyword"),
            (r"(#.*|=begin.*?^=end)", "comment"),
            (r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", "string")
        ]
        
        cpp_patterns = [
            (r"\b(auto|bool|break|case|catch|char|class|const|constexpr|continue|default|delete|do|double|else|enum|explicit|export|extern|false|final|float|for|friend|goto|if|inline|int|long|mutable|namespace|new|nullptr|operator|private|protected|public|register|reinterpret_cast|return|short|signed|sizeof|static|static_assert|static_cast|struct|switch|template|this|throw|true|try|typedef|typeid|typename|union|unsigned|using|virtual|void|volatile|wchar_t|while)\b", "keyword"),
            (r"(//.*|/\*.*?\*/)", "comment"),
            (r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", "string")
        ]
        
        lua_patterns = [
            (r"\b(and|break|do|else|elseif|end|false|for|function|goto|if|in|local|nil|not|or|repeat|return|then|true|until|while)\b", "keyword"),
            (r"(--.*)", "comment"),
            (r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", "string")
        ]
        
        luau_patterns = [
            (r"\b(and|break|elseif|else|end|false|for|function|if|in|local|nil|not|or|repeat|then|true|until|while|class|continue|extends|implements|interface|readonly|abstract|struct|enum|instanceof|import|module|export|package|using|from|as|yield)\b", "keyword"),
            (r"(--.*)", "comment"),
            (r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", "string")
        ]
        
        if self.current_language == "python":
            return python_patterns
        elif self.current_language == "csharp":
            return csharp_patterns
        elif self.current_language == "ruby":
            return ruby_patterns
        elif self.current_language == "cpp":
            return cpp_patterns
        elif self.current_language == "lua":
            return lua_patterns
        elif self.current_language == "luau":
            return luau_patterns
        return []
    
    def new_file(self):
        self.filename = None
        self.current_language = None
        self.text_area.delete(1.0, tk.END)
    
    def open_file(self):
        self.filename = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("All Files", "*.*"), ("Text Documents", "*.txt")])
        if self.filename:
            self.master.title(f"ScottCodiN IDE - {os.path.basename(self.filename)}")
            self.text_area.delete(1.0, tk.END)
            with open(self.filename, "r") as file:
                self.text_area.insert(1.0, file.read())
            self.set_language()
            self.highlight_syntax()
    
    def save_file(self):
        if self.filename:
            content = self.text_area.get(1.0, tk.END)
            with open(self.filename, "w") as file:
                file.write(content)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        self.filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("All Files", "*.*"), ("Text Documents", "*.txt")])
        if self.filename:
            self.master.title(f"ScottCodiN IDE - {os.path.basename(self.filename)}")
            content = self.text_area.get(1.0, tk.END)
            with open(self.filename, "w") as file:
                file.write(content)
    
    def exit_ide(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.master.destroy()
    
    def edit_action(self, action: str):
        if action == 'cut':
            self.text_area.event_generate("<<Cut>>")
        elif action == 'copy':
            self.text_area.event_generate("<<Copy>>")
        elif action == 'paste':
            self.text_area.event_generate("<<Paste>>")
        elif action == 'delete':
            self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
    
    def show_about(self):
        messagebox.showinfo("About", "ScottCodiN IDE\nA simple code editor built with Tkinter\nSupports Python, C#, Ruby, C++, Lua, and Luau syntax highlighting")
    
    def show_help(self):
        messagebox.showinfo("Help", "ScottCodiN IDE Help\nThis IDE supports various features such as syntax highlighting, undo/redo, file operations, and more. For further assistance, refer to the documentation or contact support.")
    
    def open_guide(self):
        webbrowser.open_new("https://foundation-scott.vercel.app/scottcodin-help.html")
    
    def show_error(self, message: str):
        self.text_area.tag_configure("error", foreground="red")
        self.text_area.tag_add("error", "insert linestart", "insert lineend")
        messagebox.showerror("Error", message)
    
    def setup_tags(self):
        self.text_area.tag_configure("keyword", foreground="blue")
        self.text_area.tag_configure("builtin", foreground="purple")
        self.text_area.tag_configure("comment", foreground="green")
        self.text_area.tag_configure("string", foreground="orange")
    
    def update_scroll_region(self, event=None):
    	if self.text_area.get("1.0", tk.END) != "\n":
        	self.text_area.config(scrollregion=self.text_area.bbox("all"))
    
    def scroll_up(self, event):
        self.text_area.yview_scroll(-1, "units")
    
    def scroll_down(self, event):
        self.text_area.yview_scroll(1, "units")
    
    def start_select_all_timer(self, event):
        self.select_all_timer = self.master.after(3000, self.select_all)
    
    def stop_select_all_timer(self, event):
        if self.select_all_timer is not None:
            self.master.after_cancel(self.select_all_timer)
    
    def select_all(self):
        self.text_area.tag_add("sel", "1.0", "end-1c")

if __name__ == "__main__":
    root = tk.Tk()
    ide = CodeIDE(root)
    ide.setup_tags()
    root.mainloop()
