from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.animation import Animation
from kivy.properties import ListProperty
import time


PRIMARY_BLUE = (0.16, 0.47, 0.75, 1)      #  основной голубой
SECONDARY_BLUE = (0.33, 0.67, 0.93, 1)    # светлый голубой
LIGHT_BG = (0.95, 0.97, 1.0, 1)         #фоновый цвет
DARK_TEXT = (0.12, 0.14, 0.16, 1)         # текст
WHITE = (1, 1, 1, 1)                    # Чистый белый
START_COLOR = (0.18, 0.8, 0.44, 1)      #зеленый (начало)
END_COLOR = (0.91, 0.3, 0.24, 1)        # красный (конец)
HIGHLIGHT = (0.99, 0.83, 0.24, 0.85)     #  выделение
CELL_COLOR = (0.98, 0.99, 1.0, 1)        #цвет клеток
BORDER_COLOR = (0.8, 0.85, 0.9, 1)       #границы клеток
RESULT_BG = (0.92, 0.95, 1.0, 1)        #фон результатов

#клава
RUSSIAN_KEYMAP = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н',
    'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
    'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р',
    'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
    'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т',
    'm': 'ь', ',': 'б', '.': 'ю', '/': '.', '`': 'ё'
}

Window.clearcolor = LIGHT_BG

class HighlightButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_bg = self.background_color
        self.default_color = DARK_TEXT

    def highlight(self, color, duration=0.1):
        self.background_color = color
        self.color = WHITE

    def reset_color(self):
        self.background_color = self.default_bg
        self.color = DARK_TEXT

class WordGrid(GridLayout):
    current_path = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 5
        self.rows = 5
        self.cells = []
        self.current_cell = 0
        self.cell_size = 60
        self.size_hint = (None, None)
        self.width = self.cell_size * 5
        self.height = self.cell_size * 5
        self.pos_hint = {'center_x': 0.5}
        self.create_grid()

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def create_grid(self):
        self.cells = []
        self.clear_widgets()
        for _ in range(25):
            cell = HighlightButton(
                text='',
                font_size=24,
                size_hint=(None, None),
                size=(self.cell_size, self.cell_size),
                background_normal='',
                background_color=CELL_COLOR,
                color=DARK_TEXT,
                bold=True
            )
            with cell.canvas.before:
                Color(*BORDER_COLOR)
                cell.border_rect = Rectangle(pos=cell.pos, size=cell.size)
            cell.bind(pos=self.update_border_rect)
            cell.bind(size=self.update_border_rect)
            self.cells.append(cell)
            self.add_widget(cell)

    def update_border_rect(self, instance, value):
        instance.border_rect.pos = instance.pos
        instance.border_rect.size = instance.size

    def get_cell(self, row, col):
        if 0 <= row < 5 and 0 <= col < 5:
            return self.cells[row * 5 + col]
        return None

    def get_letter(self, row, col):
        cell = self.get_cell(row, col)
        return cell.text if cell else ''

    def show_path(self, path):
        for cell in self.cells:
            cell.reset_color()
        
        if not path:
            return
            
        self.current_path = path
        total = len(path)
        
        for i, (row, col) in enumerate(path):
            cell = self.get_cell(row, col)
            if cell:
                ratio = i / max(1, total-1)
                color = (
                    START_COLOR[0] + (END_COLOR[0] - START_COLOR[0]) * ratio,
                    START_COLOR[1] + (END_COLOR[1] - START_COLOR[1]) * ratio,
                    START_COLOR[2] + (END_COLOR[2] - START_COLOR[2]) * ratio,
                    1
                )
                cell.highlight(color)

    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1].lower()
        russian_char = RUSSIAN_KEYMAP.get(key, None)
        
        if russian_char and self.current_cell < len(self.cells):
            self.cells[self.current_cell].text = russian_char.upper()
            self.current_cell += 1
        elif key == 'backspace':
            if self.current_cell > 0:
                self.current_cell -= 1
                self.cells[self.current_cell].text = ''
        elif key == 'enter':
            app = App.get_running_app()
            if not app.sorted_words:
                app.find_words(None)
            else:
                app.show_next_word(None)
        return True

class ScrollableLabel(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*RESULT_BG)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        self.layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)
        self.word_paths = {}
        self.current_word_index = 0
        
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def add_word(self, word, path):
        btn = Button(
            text=f"{word} (длина: {len(word)})",
            size_hint_y=None,
            height=40,
            background_color=WHITE,
            color=DARK_TEXT,
            bold=True,
            background_normal=''
        )
        with btn.canvas.before:
            Color(*BORDER_COLOR)
            Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=1)
        
        btn.word = word
        btn.path = path
        btn.bind(on_press=self.highlight_word)
        self.layout.add_widget(btn)
        self.word_paths[word] = path

    def highlight_word(self, instance):
        app = App.get_running_app()
        app.show_word(instance.word, instance.path)

    def clear(self):
        self.layout.clear_widgets()
        self.word_paths = {}
        self.current_word_index = 0

class MainLayout(BoxLayout):
    pass

class WordAssistantApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.word_trie = {}
        self.found_words = {}  
        self.sorted_words = []
        self.current_word_index = 0
        self.load_dictionary()
        self.cell_size = 60
        self.padding = 20

    def load_dictionary(self):
        start_time = time.time()
        try:
            with open("russian_utf8.txt", 'r', encoding='utf-8') as file:
                for word in file:
                    word = word.strip().upper().replace('Ё', 'Е')
                    if 2 <= len(word) <= 15 and word.isalpha():
                        self._add_to_trie(word)
            print(f"Словарь загружен за {time.time() - start_time:.2f} сек")
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
#Trie структура даннфх
    def _add_to_trie(self, word):
        node = self.word_trie
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node['$'] = True

    def build(self):
        grid_width = self.cell_size * 5
        grid_height = self.cell_size * 5
        window_width = grid_width + 2 * self.padding
        window_height = grid_height + 350
        
        Window.size = (window_width, window_height)
        Window.minimum_width = window_width
        Window.minimum_height = window_height

        main_layout = MainLayout(orientation='vertical', padding=10, spacing=10)
        
        self.word_grid = WordGrid(size_hint=(1, None), height=grid_height)
        main_layout.add_widget(self.word_grid)

        controls = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        
        self.clear_button = Button(
            text='Очистить поле',
            background_color=SECONDARY_BLUE,
            color=WHITE,
            bold=True,
            font_size=16
        )
        self.clear_button.bind(on_press=self.clear_grid)
        
        self.search_button = Button(
            text='Найти слова',
            background_color=PRIMARY_BLUE,
            color=WHITE,
            bold=True,
            font_size=16
        )
        self.search_button.bind(on_press=self.find_words)
        
        controls.add_widget(self.clear_button)
        controls.add_widget(self.search_button)
        main_layout.add_widget(controls)

        self.results_scroll = ScrollableLabel(size_hint=(1, 1))
        main_layout.add_widget(self.results_scroll)

        self.counter_label = Label(
            text='Найдено слов: 0',
            size_hint=(1, None),
            height=30,
            color=DARK_TEXT,
            bold=True,
            font_size=14
        )
        main_layout.add_widget(self.counter_label)

        nav_buttons = BoxLayout(size_hint=(1, None), height=40, spacing=5)
        
        self.prev_button = Button(
            text='← Предыдущее',
            background_color=SECONDARY_BLUE,
            color=WHITE,
            bold=True
        )
        self.prev_button.bind(on_press=self.show_prev_word)
        
        self.next_button = Button(
            text='Следующее →',
            background_color=PRIMARY_BLUE,
            color=WHITE,
            bold=True
        )
        self.next_button.bind(on_press=self.show_next_word)
        
        nav_buttons.add_widget(self.prev_button)
        nav_buttons.add_widget(self.next_button)
        main_layout.add_widget(nav_buttons)

        return main_layout

    def clear_grid(self, instance):
        self.word_grid.current_cell = 0
        for cell in self.word_grid.cells:
            cell.text = ''
            cell.reset_color()
        self.results_scroll.clear()
        self.counter_label.text = 'Найдено слов: 0'
        self.found_words = {}
        self.sorted_words = []
        self.current_word_index = 0
#главный поиск
    def find_words(self, instance):
        start_time = time.time()
        grid = [
            [self.word_grid.get_letter(row, col) or '' for col in range(5)]
            for row in range(5)
        ]
        
        self.found_words = {}
        
        for row in range(5):
            for col in range(5):
                if grid[row][col]:
                    self._fast_search(
                        grid, row, col, 
                        grid[row][col], 
                        [(row, col)], 
                        self.word_trie.get(grid[row][col], {}), 
                        self.found_words
                    )
        
        self.results_scroll.clear()
        
        if not self.found_words:
            self.counter_label.text = 'Найдено слов: 0'
            self.results_scroll.layout.add_widget(Label(
                text="[color=ff0000]Нет вариантов :([/color]",
                markup=True,
                size_hint_y=None,
                height=40
            ))
        else:
            self.sorted_words = sorted(self.found_words.items(), key=lambda x: (-len(x[0]), x[0]))
            
            for word, path in self.sorted_words:
                self.results_scroll.add_word(word, path)
            
            self.counter_label.text = f'Найдено слов: {len(self.found_words)}'
            
            if self.sorted_words:
                self.current_word_index = 0
                self.show_word(self.sorted_words[0][0], self.sorted_words[0][1])
        
        print(f"Поиск завершен за {time.time() - start_time:.2f} сек")
#рекурсивный поиск поэтому и ыстрый
    def _fast_search(self, grid, row, col, current_word, path, trie_node, found_words):
        if '$' in trie_node and len(current_word) >= 2:
            found_words[current_word] = path.copy()
        
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                nr, nc = row + dr, col + dc
                if 0 <= nr < 5 and 0 <= nc < 5 and (nr, nc) not in path and grid[nr][nc]:
                    next_char = grid[nr][nc]
                    if next_char in trie_node:
                        new_path = path + [(nr, nc)]
                        self._fast_search(
                            grid, nr, nc, 
                            current_word + next_char, 
                            new_path, 
                            trie_node[next_char], 
                            found_words
                        )

    def show_word(self, word, path):
        self.word_grid.show_path(path)
        
        for idx, child in enumerate(self.results_scroll.layout.children):
            if hasattr(child, 'word') and child.word == word:
                self.results_scroll.scroll_to(child)
                break

    def show_next_word(self, instance):
        if not self.sorted_words:
            return
            
        self.current_word_index = (self.current_word_index + 1) % len(self.sorted_words)
        word, path = self.sorted_words[self.current_word_index]
        self.show_word(word, path)

    def show_prev_word(self, instance):
        if not self.sorted_words:
            return
            
        self.current_word_index = (self.current_word_index - 1) % len(self.sorted_words)
        word, path = self.sorted_words[self.current_word_index]
        self.show_word(word, path)

if __name__ == '__main__':
    WordAssistantApp().run()