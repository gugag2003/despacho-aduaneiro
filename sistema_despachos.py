import os
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from PIL import Image, ImageTk

# Configuração do banco de dados
conn = sqlite3.connect('despachos.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS Clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_cliente TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS Fornecedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_fornecedor TEXT NOT NULL,
    cliente_id INTEGER,
    FOREIGN KEY(cliente_id) REFERENCES Clientes(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS Processos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referencia_interna TEXT NOT NULL,
    cliente_id INTEGER,
    responsavel TEXT,
    adquirente TEXT,
    tipo TEXT,
    modal TEXT,
    fornecedor_id INTEGER,
    FOREIGN KEY(cliente_id) REFERENCES Clientes(id),
    FOREIGN KEY(fornecedor_id) REFERENCES Fornecedores(id)
)
''')

# Verificar e adicionar a coluna fornecedor_id se não existir
try:
    c.execute("SELECT fornecedor_id FROM Processos LIMIT 1")
except sqlite3.OperationalError:
    c.execute("ALTER TABLE Processos ADD COLUMN fornecedor_id INTEGER")
    conn.commit()

conn.commit()

# Funções Utilitárias
def gerar_referencia_interna(cliente_nome):
    ano = datetime.now().year % 100
    c.execute("SELECT COUNT(*) FROM Processos")
    count = c.fetchone()[0] + 1
    referencia = f"{cliente_nome[:3].upper()}{ano:02d}{count:04d}"
    return referencia

# GUI
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Despachos Aduaneiros")
        self.root.geometry("1024x768")
        self.root.state('zoomed')
        self.root.configure(bg="#222831")

        # Estilo geral
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#222831")
        self.style.configure("TLabel", background="#222831", foreground="#EEEEEE", font=("Roboto", 10))
        self.style.configure("TEntry", font=("Roboto", 10))
        self.style.configure("TButton", background="#76ABAE", foreground="#222831", font=("Roboto", 10))
        self.style.configure("TTreeview", background="#393E46", foreground="#EEEEEE", fieldbackground="#393E46", font=("Roboto", 10))
        self.style.configure("TCombobox", font=("Roboto", 10))
        self.style.map("TButton", background=[('active', '#76ABAE')])

        self.create_main_screen()
        self.create_cliente_screen()
        self.create_fornecedor_screen()
        self.create_processo_screen()

        self.create_menu()

    def create_menu(self):
        self.menu_frame = ttk.Frame(self.root, width=200, relief="raised")
        self.menu_frame.grid(row=0, column=0, sticky="ns")
        self.menu_frame.grid_propagate(False)

        self.add_menu_button("Tela Principal", "list-ul-svgrepo-com.png", self.show_main_frame)
        self.add_menu_button("Cadastrar Cliente", "add-profile-svgrepo-com.png", self.show_cliente_frame)
        self.add_menu_button("Cadastrar Processo", "add-folder-svgrepo-com.png", self.show_processo_frame)
        self.add_menu_button("Cadastrar Fornecedor", "add-node-svgrepo-com.png", self.show_fornecedor_frame)

    def add_menu_button(self, text, icon, command):
        # Ajuste o caminho relativo baseado na localização do script
        base_dir = os.path.dirname(__file__)
        icon_path = os.path.join(base_dir, icon)
        image = Image.open(icon_path)
        image = image.resize((30, 30), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        button = ttk.Button(self.menu_frame, text=text, image=photo, compound="left", command=command, style="TButton")
        button.image = photo
        button.pack(fill='x', pady=5)

    def create_main_screen(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        self.tree = ttk.Treeview(self.main_frame, columns=("referencia_interna", "cliente", "responsavel", "adquirente", "fornecedor", "tipo", "modal"), show='headings')
        self.tree.heading("referencia_interna", text="Referência Interna")
        self.tree.heading("cliente", text="Cliente")
        self.tree.heading("responsavel", text="Responsável Imp/Exp")
        self.tree.heading("adquirente", text="Adquirente")
        self.tree.heading("fornecedor", text="Fornecedor")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("modal", text="Modal")
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.load_processos()

    def create_cliente_screen(self):
        self.cliente_frame = ttk.Frame(self.root)

        ttk.Label(self.cliente_frame, text="Nome do Cliente:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.nome_cliente_entry = ttk.Entry(self.cliente_frame)
        self.nome_cliente_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ttk.Button(self.cliente_frame, text="Adicionar Cliente", command=self.add_cliente).grid(row=1, column=0, columnspan=2, pady=10)

        self.cliente_frame.grid_columnconfigure(0, weight=1)
        self.cliente_frame.grid_columnconfigure(1, weight=1)

    def create_fornecedor_screen(self):
        self.fornecedor_frame = ttk.Frame(self.root)

        ttk.Label(self.fornecedor_frame, text="Nome do Fornecedor:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.nome_fornecedor_entry = ttk.Entry(self.fornecedor_frame)
        self.nome_fornecedor_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.fornecedor_frame, text="Cliente:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.fornecedor_cliente_var = tk.StringVar()
        self.fornecedor_cliente_dropdown = ttk.Combobox(self.fornecedor_frame, textvariable=self.fornecedor_cliente_var)
        self.fornecedor_cliente_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.load_clientes_for_fornecedor()

        ttk.Button(self.fornecedor_frame, text="Adicionar Fornecedor", command=self.add_fornecedor).grid(row=2, column=0, columnspan=2, pady=10)

        self.fornecedor_frame.grid_columnconfigure(0, weight=1)
        self.fornecedor_frame.grid_columnconfigure(1, weight=1)

    def create_processo_screen(self):
        self.processo_frame = ttk.Frame(self.root)

        ttk.Label(self.processo_frame, text="Cliente:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.cliente_var = tk.StringVar()
        self.cliente_dropdown = ttk.Combobox(self.processo_frame, textvariable=self.cliente_var)
        self.cliente_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.cliente_dropdown.bind("<<ComboboxSelected>>", self.on_cliente_selected)
        self.load_clientes()

        ttk.Label(self.processo_frame, text="Referência Interna:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.referencia_interna_entry = ttk.Entry(self.processo_frame, state='readonly')
        self.referencia_interna_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.processo_frame, text="Responsável Imp/Exp:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.responsavel_entry = ttk.Entry(self.processo_frame)
        self.responsavel_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.responsavel_cliente_var = tk.IntVar()
        self.responsavel_checkbox = ttk.Checkbutton(self.processo_frame, text="Responsável é o cliente", variable=self.responsavel_cliente_var, command=self.toggle_responsavel)
        self.responsavel_checkbox.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.processo_frame, text="Adquirente:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
        self.adquirente_entry = ttk.Entry(self.processo_frame)
        self.adquirente_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        self.adquirente_cliente_var = tk.IntVar()
        self.adquirente_checkbox = ttk.Checkbutton(self.processo_frame, text="Adquirente é o cliente", variable=self.adquirente_cliente_var, command=self.toggle_adquirente)
        self.adquirente_checkbox.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.processo_frame, text="Fornecedor:").grid(row=6, column=0, padx=10, pady=10, sticky="e")
        self.fornecedor_var = tk.StringVar()
        self.fornecedor_dropdown = ttk.Combobox(self.processo_frame, textvariable=self.fornecedor_var)
        self.fornecedor_dropdown.grid(row=6, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.processo_frame, text="Tipo:").grid(row=7, column=0, padx=10, pady=10, sticky="e")
        self.tipo_var = tk.StringVar()
        self.tipo_dropdown = ttk.Combobox(self.processo_frame, textvariable=self.tipo_var, values=["Importação", "Exportação"])
        self.tipo_dropdown.grid(row=7, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.processo_frame, text="Modal:").grid(row=8, column=0, padx=10, pady=10, sticky="e")
        self.modal_var = tk.StringVar()
        self.modal_dropdown = ttk.Combobox(self.processo_frame, textvariable=self.modal_var, values=["Aéreo", "Marítimo", "Rodoviário"])
        self.modal_dropdown.grid(row=8, column=1, padx=10, pady=10, sticky="w")

        ttk.Button(self.processo_frame, text="Adicionar Processo", command=self.add_processo).grid(row=9, column=0, columnspan=2, pady=10)

        self.processo_frame.grid_columnconfigure(0, weight=1)
        self.processo_frame.grid_columnconfigure(1, weight=1)

    def load_clientes(self):
        c.execute("SELECT nome_cliente FROM Clientes")
        clientes = [row[0] for row in c.fetchall()]
        self.cliente_dropdown['values'] = clientes

    def load_clientes_for_fornecedor(self):
        c.execute("SELECT nome_cliente FROM Clientes")
        clientes = [row[0] for row in c.fetchall()]
        self.fornecedor_cliente_dropdown['values'] = clientes

    def load_fornecedores(self, cliente_nome):
        c.execute('''
        SELECT nome_fornecedor 
        FROM Fornecedores 
        JOIN Clientes ON Fornecedores.cliente_id = Clientes.id 
        WHERE Clientes.nome_cliente = ?
        ''', (cliente_nome,))
        fornecedores = [row[0] for row in c.fetchall()]
        self.fornecedor_dropdown['values'] = fornecedores

    def load_processos(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        c.execute('''
        SELECT Processos.referencia_interna, Clientes.nome_cliente, Processos.responsavel, 
               Processos.adquirente, Fornecedores.nome_fornecedor, Processos.tipo, Processos.modal
        FROM Processos
        JOIN Clientes ON Processos.cliente_id = Clientes.id
        JOIN Fornecedores ON Processos.fornecedor_id = Fornecedores.id
        ''')

        for row in c.fetchall():
            self.tree.insert("", "end", values=row)

    def add_cliente(self):
        nome_cliente = self.nome_cliente_entry.get()
        if nome_cliente:
            c.execute("INSERT INTO Clientes (nome_cliente) VALUES (?)", (nome_cliente,))
            conn.commit()
            self.load_clientes()
            self.load_clientes_for_fornecedor()
            messagebox.showinfo("Sucesso", "Cliente adicionado com sucesso!")
            self.nome_cliente_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", "O nome do cliente não pode estar vazio!")

    def add_fornecedor(self):
        nome_fornecedor = self.nome_fornecedor_entry.get()
        cliente_nome = self.fornecedor_cliente_var.get()
        if nome_fornecedor and cliente_nome:
            c.execute("SELECT id FROM Clientes WHERE nome_cliente=?", (cliente_nome,))
            cliente_id = c.fetchone()[0]
            c.execute("INSERT INTO Fornecedores (nome_fornecedor, cliente_id) VALUES (?, ?)", (nome_fornecedor, cliente_id))
            conn.commit()
            messagebox.showinfo("Sucesso", "Fornecedor adicionado com sucesso!")
            self.nome_fornecedor_entry.delete(0, tk.END)
            self.fornecedor_cliente_var.set("")
        else:
            messagebox.showerror("Erro", "O nome do fornecedor e o cliente não podem estar vazios!")

    def add_processo(self):
        cliente_nome = self.cliente_var.get()
        adquirente = self.adquirente_entry.get()
        fornecedor_nome = self.fornecedor_var.get()
        tipo = self.tipo_var.get()
        modal = self.modal_var.get()
        responsavel = self.responsavel_entry.get()

        if cliente_nome and adquirente and fornecedor_nome and tipo and modal and responsavel:
            referencia_interna = self.referencia_interna_entry.get()
            c.execute("SELECT id FROM Clientes WHERE nome_cliente=?", (cliente_nome,))
            cliente_id = c.fetchone()[0]
            c.execute("SELECT id FROM Fornecedores WHERE nome_fornecedor=?", (fornecedor_nome,))
            fornecedor_id = c.fetchone()[0]

            c.execute('''
            INSERT INTO Processos (referencia_interna, cliente_id, responsavel, adquirente, fornecedor_id, tipo, modal) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (referencia_interna, cliente_id, responsavel, adquirente, fornecedor_id, tipo, modal))
            conn.commit()

            self.load_processos()
            messagebox.showinfo("Sucesso", "Processo adicionado com sucesso!")
            self.clear_processo_fields()
        else:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos!")

    def clear_processo_fields(self):
        self.cliente_var.set("")
        self.referencia_interna_entry.config(state='normal')
        self.referencia_interna_entry.delete(0, tk.END)
        self.referencia_interna_entry.config(state='readonly')
        self.responsavel_entry.delete(0, tk.END)
        self.adquirente_entry.delete(0, tk.END)
        self.fornecedor_var.set("")
        self.tipo_var.set("")
        self.modal_var.set("")
        self.responsavel_cliente_var.set(0)
        self.adquirente_cliente_var.set(0)

    def toggle_responsavel(self):
        if self.responsavel_cliente_var.get() == 1:
            self.responsavel_entry.delete(0, tk.END)
            self.responsavel_entry.insert(0, self.cliente_var.get())
        else:
            self.responsavel_entry.delete(0, tk.END)

    def toggle_adquirente(self):
        if self.adquirente_cliente_var.get() == 1:
            self.adquirente_entry.delete(0, tk.END)
            self.adquirente_entry.insert(0, self.cliente_var.get())
        else:
            self.adquirente_entry.delete(0, tk.END)

    def on_cliente_selected(self, event):
        cliente_nome = self.cliente_var.get()
        referencia_interna = gerar_referencia_interna(cliente_nome)
        self.referencia_interna_entry.config(state='normal')
        self.referencia_interna_entry.delete(0, tk.END)
        self.referencia_interna_entry.insert(0, referencia_interna)
        self.referencia_interna_entry.config(state='readonly')
        self.load_fornecedores(cliente_nome)

    def show_main_frame(self):
        self.cliente_frame.grid_forget()
        self.processo_frame.grid_forget()
        self.fornecedor_frame.grid_forget()
        self.main_frame.grid(row=0, column=1, sticky="nsew")

    def show_cliente_frame(self):
        self.main_frame.grid_forget()
        self.processo_frame.grid_forget()
        self.fornecedor_frame.grid_forget()
        self.cliente_frame.grid(row=0, column=1, sticky="nsew")

    def show_fornecedor_frame(self):
        self.main_frame.grid_forget()
        self.processo_frame.grid_forget()
        self.cliente_frame.grid_forget()
        self.fornecedor_frame.grid(row=0, column=1, sticky="nsew")

    def show_processo_frame(self):
        self.main_frame.grid_forget()
        self.cliente_frame.grid_forget()
        self.fornecedor_frame.grid_forget()
        self.processo_frame.grid(row=0, column=1, sticky="nsew")

root = tk.Tk()
app = App(root)

root.mainloop()
