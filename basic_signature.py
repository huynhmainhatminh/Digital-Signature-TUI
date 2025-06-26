import random
import math
import hashlib
from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Static, Label, Header, TextArea
from textual.containers import Vertical, Horizontal, Container, HorizontalScroll, VerticalScroll
from textual.color import Color
from textual.screen import ModalScreen, Screen
from textual.theme import Theme, BUILTIN_THEMES as TEXTUAL_THEMES
from textual import on
from tkinter.filedialog import askopenfilename

galaxy_primary = Color.parse("#C45AFF")
galaxy_secondary = Color.parse("#a684e8")
galaxy_warning = Color.parse("#FFD700")
galaxy_error = Color.parse("#FF4500")
galaxy_success = Color.parse("#00FA9A")
galaxy_accent = Color.parse("#FF69B4")
galaxy_background = Color.parse("#0F0F1F")
galaxy_surface = Color.parse("#1E1E3F")
galaxy_panel = Color.parse("#2D2B55")
galaxy_contrast_text = galaxy_background.get_contrast_text(1.0)

galaxy_theme = Theme(
    name="galaxy",
    primary=galaxy_primary.hex,
    secondary=galaxy_secondary.hex,
    warning=galaxy_warning.hex,
    error=galaxy_error.hex,
    success=galaxy_success.hex,
    accent=galaxy_accent.hex,
    background=galaxy_background.hex,
    surface=galaxy_surface.hex,
    panel=galaxy_panel.hex,
    dark=True,
    variables={
        "input-cursor-background": "#C45AFF",
        "footer-background": "transparent",
    },
)


def mod_inverse(e, phi):
    """Tính nghịch đảo modulo của e mod phi bằng thuật toán Euclid mở rộng."""

    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y

    _, d, _ = extended_gcd(e, phi)
    if d < 0:
        d += phi
    return d


def choose_e(phi):
    """Chọn số e nguyên tố cùng nhau với phi(n), ưu tiên các giá trị nhỏ."""
    # Danh sách các giá trị e phổ biến (các số nguyên tố nhỏ)
    common_e_values = [3, 5, 17, 257, 65537]

    # Thử các giá trị e phổ biến trước
    for e in common_e_values:
        if 1 < e < phi and math.gcd(e, phi) == 1:
            return e

    # Nếu không tìm được e phổ biến, tìm số e ngẫu nhiên
    max_attempts = 100
    for _ in range(max_attempts):
        # Chọn e ngẫu nhiên trong khoảng [3, phi)
        e = random.randrange(3, phi, 2)  # Chỉ chọn số lẻ để tối ưu
        if math.gcd(e, phi) == 1:
            return e


def mod_pow(base, exponent, modulus):
    """Tính lũy thừa modulo nhanh (base^exponent mod modulus)."""
    result = 1
    base = base % modulus
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulus
        base = (base * base) % modulus
        exponent >>= 1
    return result



def verify_signature(hash256, signature, public_key):
    """Xác minh chữ ký số bằng khóa công khai và SHA-256 (hexdigest)."""
    n, e = public_key
    h_int = int(hash256, 16) % n
    h_prime = mod_pow(signature, e, n)
    # So sánh h và h'
    return h_int == h_prime


def sign_message(private_key, hash256):
    """Ký chữ ký số cho thông điệp bằng khóa bí mật và SHA-256 (hexdigest)."""
    n, d = private_key
    # Chuyển chuỗi hex thành số nguyên
    h_int = int(hash256, 16) % n
    # Tính chữ ký: s = h^d mod n
    signature = mod_pow(h_int, d, n)
    return signature


def hash_file_256(message):
    h = hashlib.sha256(message.encode('utf-8')).hexdigest()
    return h



class ErrorMessageScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    ErrorMessageScreen {
        align: center middle;
        & > Vertical {
            background: $background-lighten-1;
            padding: 1 2;
            width: auto;
            height: 25%;
            border: round $primary;
        }
        #error-message {
        
            background: transparent;
            color: #FF0000;
            text-align: center;
            height: 1fr;
            content-align: center middle;
        }
        
        #correct-message {
            background: transparent;
            color: #00FF99;
            text-align: center;
            height: 1fr;
            content-align: center middle;
        }
        
        #close {
            margin-top: 1;
            align: center middle;
            width: 1fr;
            content-align: center middle;
        }
    }
    """

    BINDINGS = [
        ("escape", "dismiss('')", "Close error popup"),
    ]

    def __init__(self, message: str, id_css: str):
        super().__init__()
        self.message = message
        self.id_css = id_css

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.message, id=self.id_css)
            yield Button("Đóng", id="close")

    @on(Button.Pressed, "#close")
    def on_close(self) -> None:
        self.app.pop_screen()


class Random_Prime:
    def __init__(self) -> None:
        self.min_val: int = 10
        self.max_val: int = 100

    @staticmethod
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    def generate_random_prime(self):

        primes = [num for num in range(max(self.min_val, 2), self.max_val + 1) if self.is_prime(num)]

        return random.choice(primes)


class Apps(App):

    def __init__(self):
        super().__init__()
        self.public_key = (0, 0)
        self.private_key = (0, 0)

        self.data_sender = ""
        self.data_receiver = ""

        self.data_hash_sender = ""
        self.data_hash_receiver = ""

        self.data_sign_sender = ""

    CSS = """

    Container#app-container {
        layout: vertical; /* Sắp xếp dọc để chứa tiêu đề và nội dung */
        width: 100%;
        height: 100%;
        background: $panel-darken-3; /* Nền tối giống theme galaxy */
        padding: 1;
    }

    Vertical {
        width: auto;
    }


    Horizontal {
        width: auto;
    }

    Input {
        margin: 1;
        border: round $primary;
        background: transparent;
    }

    Label {

        width: auto;
        margin: 1;
        color: $text;
    }

    Button {
        margin: 0 1; /* Khoảng cách giữa các nút */
        width: auto;
        border: round $primary;
        background: transparent;
    }

    Static {
        margin: 1;
        width: auto; 
    }

    Vertical#menu {
        height: 14;
        width: 74;
        padding: 1 1;
        border: round $primary;
    }

    Vertical#menu1 {
        padding: 0 1;
        border: round $primary;
    }

    Vertical#sender {
        padding: 1 1;
        border: round $primary;
    }

    Vertical#receiver {
        padding: 1 1;
        border: round $primary;
    }


    Input#input-p {
        width: 32;
    }

    Input#input-q {
        width: 32;
    }
    
    
    Input#input-signature {
        width: 66;
    }

    Button#btn1 {
        border: round #00FF99;
        color: #00FF99;
    }

    Button#btn2 {
        border: round #FFD700;
        color: #FFD700;
    }

    Button#btn3 {
        border: round #FF0000;
        color: #FF0000;
    }


    Label#label-p {
        width: 36;
        margin-bottom: 1;
        text-align: center;
    }

    Label#label-q {
        width: 36;
        margin-bottom: 1;
        text-align: center;
    }

    Label#modulus-n-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }

    Label#euler-n-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }

    Label#public-e-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }

    Label#private-d-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }

    Label#key-public-n-e-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }

    Label#key-private-n-d-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }

    Label#sender-sha-256 {
        width: 22;
        text-align: center;
        border: round $primary;
    }


    Label#sender-signature-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }


    Label#receiver-sha-256 {
        width: 22;
        text-align: center;
        border: round $primary;
    }

    Label#receiver-signature-label {
        width: 22;
        text-align: center;
        border: round $primary;
    }


    Horizontal#button-container {
        width: 70;
        align: center middle;
    }

    Horizontal#button-receiver {
        width: 70;
        align: center bottom;
    }

    Static#modulus-n {
        border: round $primary;
        height: 3;
        width: 45; 
    }
    Static#euler-n {
        border: round $primary;
        height: 3;
        width: 45;
    }
    Static#public-e {
        border: round $primary;
        height: 3;
        width: 45;
    }
    Static#private-d {
        border: round $primary;
        height: 3;
        width: 45;
    }
    Static#key-public-n-e {
        border: round $primary;
        height: 3;
        width: 45;
    }
    Static#key-private-n-d {
        border: round $primary;
        height: 3;
        width: 45;
    }


    Static#sha-256-sender {
        border: round $primary;
        height: 3;
        width: 66;
    }


    Static#sha-256-receiver {
        border: round $primary;
        height: 3;
        width: 66;
    }


    Static#signature-sender {
        border: round $primary;
        height: 3;
        width: 66;
    }

    Static#signature-receiver {
        border: round $primary;
        height: 3;
        width: 66;
    }


    Static#upload_file_sender {
        border: round #00ffd7;
        height: 3;
        width: 66;
        margin-bottom: 2;
    }


    Static#upload_file_receiver {
        border: round #00ffd7;
        height: 3;
        width: 66;
        margin-bottom: 2;
    }

    Button#btn1-receiver {
        border: round #00FF99;
        color: #00FF99;
    }

    Button#btn4-receiver {
        border: round #00FFFF;
        color: #00FFFF;
    }

    Button#btn1-sender {
        border: round #00FF99;
        color: #00FF99;
    }

    Button#btn2-sender {
        border: round #FFD700;
        color: #FFD700;
    }

    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="app-container"):
            with Horizontal():
                with Vertical():
                    with Vertical(id="menu") as vertical:
                        vertical.border_title = "Cài Đặt"

                        with Horizontal():
                            with Vertical():
                                yield Label("Số nguyên tố bí mật p :", id="label-p")
                                yield Input(placeholder="Nhập số nguyên tố bí mật p", id="input-p")

                            with Vertical():
                                yield Label("Số nguyên tố bí mật q :", id="label-q")
                                yield Input(placeholder="Nhập số nguyên tố bí mật q", id="input-q")

                        with Horizontal(id="button-container"):
                            yield Button("Ngẫu Nhiên", id="btn1")
                            yield Button("Tính Toán", id="btn2")
                            yield Button("Làm Mới", id="btn3")

                    with Vertical(id="menu1") as vertical:
                        vertical.border_title = "Dữ Liệu"

                        with Horizontal():
                            yield Label("Modulus n", id="modulus-n-label")
                            yield Static("", id="modulus-n")

                        with Horizontal():
                            yield Label("φ(n)", id="euler-n-label")
                            yield Static("", id="euler-n")

                        with Horizontal():
                            yield Label("Số mũ công khai e", id="public-e-label")
                            yield Static("", id="public-e")

                        with Horizontal():
                            yield Label("Số mũ bí mật d", id="private-d-label")
                            yield Static("", id="private-d")

                        with Horizontal():
                            yield Label("Khóa Public (n,e)", id="key-public-n-e-label")
                            yield Static("", id="key-public-n-e")

                        with Horizontal():
                            yield Label("Khóa Private (n,d)", id="key-private-n-d-label")
                            yield Static("", id="key-private-n-d")

                with Vertical():
                    with Vertical():
                        with Vertical(id="sender") as vertical:
                            vertical.border_title = "Người Gửi"
                            with Horizontal():
                                yield Button("Tải Tệp Tin ↑", id="btn_upload_file_sender")
                                yield Static("", id="upload_file_sender")

                            with Horizontal():
                                yield Label("SHA-256", id="sender-sha-256")
                                yield Static("", id="sha-256-sender")

                            with Horizontal():
                                yield Label("Chữ ký số", id="sender-signature-label")
                                yield Static("", id="signature-sender")

                            with Horizontal(id="button-receiver"):
                                yield Button("Băm (HASH)", id="btn1-sender")
                                yield Button("Ký Số", id="btn2-sender")

                        with Vertical(id="receiver") as vertical:
                            vertical.border_title = "Người Nhận"

                            with Horizontal():
                                yield Button("Tải Tệp Tin ↑", id="btn_upload_file_receiver")
                                yield Static("", id="upload_file_receiver")

                            with Horizontal():
                                yield Label("SHA-256", id="receiver-sha-256")
                                yield Static("", id="sha-256-receiver")

                            with Horizontal():
                                yield Label("Chữ ký số", id="receiver-signature-label")
                                yield Input("", id="input-signature")

                            with Horizontal(id="button-receiver"):
                                yield Button("Băm (HASH)", id="btn1-receiver")
                                yield Button("Xác Minh", id="btn4-receiver")

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "btn1":
            input_p = self.query_one("#input-p", Input)
            input_p.value = str(Random_Prime().generate_random_prime())

            input_q = self.query_one("#input-q", Input)
            input_q.value = str(Random_Prime().generate_random_prime())

        elif event.button.id == "btn2":

            input_p_value = str(self.query_one("#input-p", Input).value)
            input_q_value = str(self.query_one("#input-q", Input).value)

            if input_p_value.isnumeric() is True and input_q_value.isnumeric() is True:

                if Random_Prime().is_prime(int(input_p_value)) is False or Random_Prime().is_prime(
                        int(input_q_value)
                        ) is False:
                    self.push_screen(ErrorMessageScreen(message="Tham số không phải là số nguyên tố.", id_css="error-message"))
                else:
                    modulus_n = int(input_q_value) * int(input_p_value)
                    euler_n = (int(input_q_value) - 1) * (int(input_p_value) - 1)

                    e = choose_e(euler_n)

                    d = mod_inverse(e, euler_n)

                    self.query_one("#modulus-n", Static).update(str(modulus_n))
                    self.query_one("#euler-n", Static).update(str(euler_n))
                    self.query_one("#public-e", Static).update(str(e))
                    self.query_one("#private-d", Static).update(str(d))
                    self.query_one("#key-public-n-e", Static).update(str(f"({modulus_n},{e})"))
                    self.query_one("#key-private-n-d", Static).update(str(f"({modulus_n},{d})"))

                    self.public_key = (modulus_n, e)
                    self.private_key = (modulus_n, d)
            else:
                self.push_screen(ErrorMessageScreen(message="Tham số không hợp lệ. Vui lòng kiểm tra lại !", id_css="error-message"))

        elif event.button.id == "btn3":
            self.query_one("#input-p", Input).value = ""
            self.query_one("#input-q", Input).value = ""
            self.query_one("#modulus-n", Static).update(str())
            self.query_one("#euler-n", Static).update(str())
            self.query_one("#public-e", Static).update(str())
            self.query_one("#private-d", Static).update(str())
            self.query_one("#key-public-n-e", Static).update(str())
            self.query_one("#key-private-n-d", Static).update(str())
            self.notify("Làm Mới Thành Công")


        elif event.button.id == "btn_upload_file_sender":
            file_path = askopenfilename(
                title="Chọn tệp .txt",
                filetypes=[("All files", "*.*")]
            )

            if file_path:
                self.query_one("#upload_file_sender", Static).update(
                    f"{file_path}"
                )
                with open(file_path, 'rb') as f:
                    self.data_sender = f.read()

                self.notify("Tải Tệp Lên Thành Công")
            else:
                self.notify("Không Có Tệp Nào Được Chọn")

        elif event.button.id == "btn1-sender":

            if self.data_sender != "":
                self.data_hash_sender = hash_file_256(message=str(self.data_sender))
                self.query_one("#sha-256-sender", Static).update(
                    f"{self.data_hash_sender}"
                )
            else:
                self.push_screen(ErrorMessageScreen(message="Vui Lòng Tải Tệp Lên", id_css="error-message"))


        elif event.button.id == "btn2-sender":
            self.data_sign_sender = sign_message(self.private_key, self.data_hash_sender)
            self.query_one("#signature-sender", Static).update(
                f"{self.data_sign_sender}"
            )

        elif event.button.id == "btn_upload_file_receiver":
            file_path = askopenfilename(
                title="Chọn tệp .txt",
                filetypes=[("All files", "*.*")]
            )

            if file_path:
                self.query_one("#upload_file_receiver", Static).update(
                    f"{file_path}"
                )

                with open(file_path, 'rb') as f:
                    self.data_receiver = f.read()

        elif event.button.id == "btn1-receiver":
            if self.data_receiver != "":
                self.data_hash_receiver = hash_file_256(message=str(self.data_receiver))
                self.query_one("#sha-256-receiver", Static).update(
                    f"{self.data_hash_receiver}"
                )
            else:
                self.push_screen(ErrorMessageScreen(message="Vui Lòng Tải Tệp Lên", id_css="error-message"))


        elif event.button.id == "btn4-receiver":
            input_signature = int(self.query_one("#input-signature", Input).value)
            is_valid = verify_signature(
                hash256=self.data_hash_receiver,
                signature=input_signature, public_key=self.public_key)

            if is_valid:
                self.push_screen(ErrorMessageScreen(message="Xác Minh Chữ Ký Hợp Lệ", id_css="correct-message"))
            else:
                self.push_screen(ErrorMessageScreen(message="Xác Minh Chữ Ký Không Hợp Lệ Hoặc Thông Điệp Giả Mạo",
                                                    id_css="error-message"))


    def on_mount(self) -> None:
        self.register_theme(galaxy_theme)
        self.theme = "galaxy"

    def action_dismiss_popup(self) -> None:
        if isinstance(self.screen, ErrorMessageScreen):
            self.pop_screen()


if __name__ == "__main__":
    app = Apps()
    app.run()