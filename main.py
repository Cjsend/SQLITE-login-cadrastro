import sqlite3
import hashlib
import re
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

DB_NAME = 'usuarios.db'

def criar_tabela():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            senha TEXT
        )
    """)
    conn.commit()
    conn.close()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def email_valido(email):
    padrao = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(padrao, email) is not None

class Cadastro(Screen):
    nome = ObjectProperty(None)
    email = ObjectProperty(None)
    senha = ObjectProperty(None)
    senha_confirma = ObjectProperty(None)
    mensagem_label = ObjectProperty(None)

    def cadastrar(self):
        app = App.get_running_app()
        app.adicionar_usuario(
            self.nome.text,
            self.email.text,
            self.senha.text,
            self.senha_confirma.text
        )
    
    def voltar_login(self):
        self.manager.current = 'login'
        self.limpar_campos()
    
    def limpar_campos(self):
        self.nome.text = ''
        self.email.text = ''
        self.senha.text = ''
        self.senha_confirma.text = ''
        self.mensagem_label.text = ''

class Listagem(Screen):
    busca_input = ObjectProperty(None)
    mensagem_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Barra de busca e ordenação
        top_bar = BoxLayout(size_hint_y=0.1, spacing=10)
        self.busca_input = TextInput(hint_text='Buscar usuário...', multiline=False)
        btn_buscar = Button(text='Buscar', size_hint_x=0.3)
        btn_buscar.bind(on_press=self.buscar)
        btn_ordenar_nome = Button(text='Ordenar por Nome', size_hint_x=0.3)
        btn_ordenar_nome.bind(on_press=lambda x: self.ordenar_por("nome"))
        btn_ordenar_email = Button(text='Ordenar por Email', size_hint_x=0.3)
        btn_ordenar_email.bind(on_press=lambda x: self.ordenar_por("email"))
        
        top_bar.add_widget(self.busca_input)
        top_bar.add_widget(btn_buscar)
        top_bar.add_widget(btn_ordenar_nome)
        top_bar.add_widget(btn_ordenar_email)
        self.layout.add_widget(top_bar)
        
        self.titulo = Label(text='Lista de Usuários', size_hint_y=0.05, font_size=24)
        self.layout.add_widget(self.titulo)
        
        self.scroll = ScrollView(size_hint=(1, 0.7))
        self.grid = GridLayout(cols=3, size_hint_y=None, spacing=10)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        
        btn_voltar = Button(text='Voltar', size_hint_y=0.1)
        btn_voltar.bind(on_press=self.voltar)
        self.layout.add_widget(btn_voltar)
        
        self.mensagem_label = Label(text='', size_hint_y=0.05, color=(1, 0, 0, 1))
        self.layout.add_widget(self.mensagem_label)
        
        self.add_widget(self.layout)
    
    def on_enter(self):
        app = App.get_running_app()
        app.listar_usuarios()
    
    def carregar_usuarios(self, usuarios):
        self.grid.clear_widgets()
        
        # Cabeçalho
        self.grid.add_widget(Label(text='Nome', bold=True))
        self.grid.add_widget(Label(text='Email', bold=True))
        self.grid.add_widget(Label(text='Ações', bold=True))
        
        for usuario in usuarios:
            id_usuario, nome, email = usuario
            
            self.grid.add_widget(Label(text=nome))
            self.grid.add_widget(Label(text=email))
            
            btn_editar = Button(text='Editar', size_hint_y=None, height=40)
            btn_editar.bind(on_press=lambda instance, id=id_usuario: self.editar_usuario(id))
            
            btn_excluir = Button(text='Excluir', size_hint_y=None, height=40)
            btn_excluir.bind(on_press=lambda instance, id=id_usuario: self.excluir_usuario(id))
            
            acoes_layout = BoxLayout(spacing=5)
            acoes_layout.add_widget(btn_editar)
            acoes_layout.add_widget(btn_excluir)
            
            self.grid.add_widget(acoes_layout)
    
    def buscar(self, instance):
        app = App.get_running_app()
        app.buscar_usuarios(self.busca_input.text)
    
    def ordenar_por(self, campo):
        app = App.get_running_app()
        app.listar_usuarios(campo)
    
    def editar_usuario(self, id_usuario):
        self.manager.get_screen('edicao').id_usuario = str(id_usuario)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email FROM usuarios WHERE id=?", (id_usuario,))
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario:
            tela_edicao = self.manager.get_screen('edicao')
            tela_edicao.nome_input.text = usuario[0]
            tela_edicao.email_input.text = usuario[1]
            tela_edicao.senha_input.text = ''
            self.manager.current = 'edicao'
    
    def excluir_usuario(self, id_usuario):
        app = App.get_running_app()
        app.deletar_usuario(id_usuario)
    
    def voltar(self, instance):
        self.manager.current = 'boasvindas'

class Edicao(Screen):
    nome_input = ObjectProperty(None)
    email_input = ObjectProperty(None)
    senha_input = ObjectProperty(None)
    mensagem_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Editar Usuário', size_hint_y=0.2, font_size=24))
        
        self.nome_input = TextInput(hint_text='Nome', multiline=False, size_hint_y=0.1)
        self.email_input = TextInput(hint_text='Email', multiline=False, size_hint_y=0.1)
        self.senha_input = TextInput(hint_text='Nova Senha (deixe em branco para manter a atual)', 
                              password=True, multiline=False, size_hint_y=0.1)
        
        layout.add_widget(self.nome_input)
        layout.add_widget(self.email_input)
        layout.add_widget(self.senha_input)
        
        btn_salvar = Button(text='Salvar', size_hint_y=0.1)
        btn_salvar.bind(on_press=self.salvar)
        
        btn_voltar = Button(text='Voltar', size_hint_y=0.1)
        btn_voltar.bind(on_press=self.voltar)
        
        layout.add_widget(btn_salvar)
        layout.add_widget(btn_voltar)
        
        self.mensagem_label = Label(text='', size_hint_y=0.1, color=(1, 0, 0, 1))
        layout.add_widget(self.mensagem_label)
        
        self.add_widget(layout)
        
        self.id_usuario = ""
    
    def salvar(self, instance):
        app = App.get_running_app()
        app.editar_usuario(
            self.id_usuario, 
            self.nome_input.text, 
            self.email_input.text, 
            self.senha_input.text
        )
    
    def voltar(self, instance):
        self.manager.current = 'listagem'
        self.limpar_campos()
    
    def limpar_campos(self):
        self.nome_input.text = ''
        self.email_input.text = ''
        self.senha_input.text = ''
        self.mensagem_label.text = ''
        self.id_usuario = ""

class Login(Screen):
    email_input = ObjectProperty(None)
    senha_input = ObjectProperty(None)
    mensagem_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Login', size_hint_y=0.3, font_size=24))
        
        self.email_input = TextInput(hint_text='Email', multiline=False, size_hint_y=0.1)
        self.senha_input = TextInput(hint_text='Senha', password=True, multiline=False, size_hint_y=0.1)
        
        layout.add_widget(self.email_input)
        layout.add_widget(self.senha_input)
        
        btn_login = Button(text='Entrar', size_hint_y=0.1)
        btn_login.bind(on_press=self.login)
        
        btn_cadastrar = Button(text='Cadastrar', size_hint_y=0.1)
        btn_cadastrar.bind(on_press=self.ir_para_cadastro)
        
        btn_resetar = Button(text='Resetar Senha', size_hint_y=0.1)
        btn_resetar.bind(on_press=self.resetar_senha)
        
        layout.add_widget(btn_login)
        layout.add_widget(btn_cadastrar)
        layout.add_widget(btn_resetar)
        
        self.mensagem_label = Label(text='', size_hint_y=0.1, color=(1, 0, 0, 1))
        layout.add_widget(self.mensagem_label)
        
        self.add_widget(layout)
    
    def login(self, instance):
        app = App.get_running_app()
        app.validar_login(self.email_input.text, self.senha_input.text)
    
    def ir_para_cadastro(self, instance):
        self.manager.current = 'cadastro'
        self.limpar_campos()
    
    def resetar_senha(self, instance):
        app = App.get_running_app()
        app.resetar_senha(self.email_input.text, self.senha_input.text)
    
    def limpar_campos(self):
        self.email_input.text = ''
        self.senha_input.text = ''
        self.mensagem_label.text = ''

class BoasVindas(Screen):
    label_boas_vindas = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.label_boas_vindas = Label(text='Bem-vindo!', font_size=24, size_hint_y=0.3)
        layout.add_widget(self.label_boas_vindas)
        
        btn_listar = Button(text='Listar Usuários', size_hint_y=0.1)
        btn_listar.bind(on_press=self.ir_para_listagem)
        
        btn_logout = Button(text='Sair', size_hint_y=0.1)
        btn_logout.bind(on_press=self.sair)
        
        layout.add_widget(btn_listar)
        layout.add_widget(btn_logout)
        
        self.add_widget(layout)
    
    def on_enter(self):
        app = App.get_running_app()
        self.label_boas_vindas.text = f'Bem-vindo, {app.nome_usuario}!'
    
    def ir_para_listagem(self, instance):
        self.manager.current = 'listagem'
    
    def sair(self, instance):
        self.manager.current = 'login'

class GerenciadorTelas(ScreenManager):
    pass

class MainApp(App):
    nome_usuario = StringProperty("")
    
    def build(self):
        criar_tabela()
        sm = GerenciadorTelas()
        sm.add_widget(Login(name="login"))
        sm.add_widget(Cadastro(name="cadastro"))
        sm.add_widget(Listagem(name="listagem"))
        sm.add_widget(Edicao(name="edicao"))
        sm.add_widget(BoasVindas(name="boasvindas"))
        return sm

    def adicionar_usuario(self, nome, email, senha, senha_confirma):
        tela_cadastro = self.root.get_screen('cadastro')
        tela_cadastro.mensagem_label.text = ""
        
        if not nome or not email or not senha:
            tela_cadastro.mensagem_label.text = "Preencha todos os campos!"
            return
            
        if senha != senha_confirma:
            tela_cadastro.mensagem_label.text = "Senhas não conferem!"
            return
            
        if not email_valido(email):
            tela_cadastro.mensagem_label.text = "Email inválido!"
            return
            
        senha_hashed = hash_senha(senha)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
            if cursor.fetchone():
                tela_cadastro.mensagem_label.text = "Email já cadastrado!"
            else:
                cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", 
                              (nome, email, senha_hashed))
                conn.commit()
                tela_cadastro.mensagem_label.text = "Usuário cadastrado com sucesso!"
                tela_cadastro.limpar_campos()
                self.root.current = 'login'
        except sqlite3.Error as e:
            tela_cadastro.mensagem_label.text = f"Erro ao acessar o banco de dados: {e}"
        finally:
            conn.close()

    def listar_usuarios(self, ordem="nome"):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, nome, email FROM usuarios ORDER BY {ordem}")
            usuarios = cursor.fetchall()
            self.root.get_screen('listagem').carregar_usuarios(usuarios)
        except sqlite3.Error as e:
            print(f"Erro ao acessar o banco de dados: {e}")
        finally:
            conn.close()

    def editar_usuario(self, id_usuario, nome, email, senha):
        tela_edicao = self.root.get_screen('edicao')
        tela_edicao.mensagem_label.text = ""
        
        if not nome or not email:
            tela_edicao.mensagem_label.text = "Preencha todos os campos!"
            return
            
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            if senha:
                senha_hashed = hash_senha(senha)
                cursor.execute("UPDATE usuarios SET nome=?, email=?, senha=? WHERE id=?", 
                              (nome, email, senha_hashed, id_usuario))
            else:
                cursor.execute("UPDATE usuarios SET nome=?, email=? WHERE id=?", 
                              (nome, email, id_usuario))
                              
            conn.commit()
            tela_edicao.mensagem_label.text = "Usuário atualizado com sucesso!"
            self.root.current = 'listagem'
        except sqlite3.Error as e:
            tela_edicao.mensagem_label.text = f"Erro ao acessar o banco de dados: {e}"
        finally:
            conn.close()
        self.listar_usuarios()

    def deletar_usuario(self, id_usuario):
        tela_listagem = self.root.get_screen('listagem')
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id=?", (id_usuario,))
            conn.commit()
            tela_listagem.mensagem_label.text = "Usuário deletado com sucesso!"
        except sqlite3.Error as e:
            tela_listagem.mensagem_label.text = f"Erro ao acessar o banco de dados: {e}"
        finally:
            conn.close()
        self.listar_usuarios()

    def validar_login(self, email, senha):
        tela_login = self.root.get_screen('login')
        tela_login.mensagem_label.text = ""
        
        if not email or not senha:
            tela_login.mensagem_label.text = "Preencha todos os campos!"
            return
            
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM usuarios WHERE email=? AND senha=?", 
                          (email, hash_senha(senha)))
            resultado = cursor.fetchone()
            if resultado:
                self.nome_usuario = resultado[1]  # Armazena o nome do usuário
                tela_login.limpar_campos()
                self.root.current = 'boasvindas'
            else:
                tela_login.mensagem_label.text = "Email ou senha incorretos!"
        except sqlite3.Error as e:
            tela_login.mensagem_label.text = f"Erro ao acessar o banco de dados: {e}"
        finally:
            conn.close()

    def buscar_usuarios(self, termo):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, email FROM usuarios WHERE nome LIKE ? OR email LIKE ? ORDER BY nome", 
                          (f"%{termo}%", f"%{termo}%"))
            usuarios = cursor.fetchall()
            self.root.get_screen('listagem').carregar_usuarios(usuarios)
        except sqlite3.Error as e:
            print(f"Erro ao acessar o banco de dados: {e}")
        finally:
            conn.close()
    
    def resetar_senha(self, email, nova_senha):
        tela_login = self.root.get_screen('login')
        if not email or not nova_senha:
            tela_login.mensagem_label.text = "Preencha todos os campos!"
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE email=?", (email,))
            if cursor.fetchone():
                cursor.execute("UPDATE usuarios SET senha=? WHERE email=?", (hash_senha(nova_senha), email))
                conn.commit()
                tela_login.mensagem_label.text = "Senha redefinida com sucesso!"
            else:
                tela_login.mensagem_label.text = "Email não encontrado!"
        except sqlite3.Error as e:
            tela_login.mensagem_label.text = f"Erro: {e}"
        finally:
            conn.close()

if __name__ == '__main__':
    MainApp().run()
