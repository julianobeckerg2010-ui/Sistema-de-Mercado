import hashlib
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk


# Parte de persistência dos dados.
# Classe responsável por abrir o banco e criar as tabelas
# e executar as operações de usuários, produtos e pedidos.
class BancoMercado:
    def __init__(self, caminho_banco="mercado_real.db"):
        # Abre a conexão com o banco SQLite.
        self.con = sqlite3.connect(caminho_banco)

        # Configura o acesso aos resultados pelo nome da coluna,
        # o que facilita o uso dos dados.
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

        # Garante que as tabelas existam ao iniciar o banco.
        self.criar_tabelas()

        # Garante que os dados iniciais estejam disponíveis.
        self.popular_dados_iniciais()

    def criar_tabelas(self):
        # Tabela de usuários.
        # Guarda dono, funcionário e cliente.
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL
            )
            """
        )

        # Tabela de produtos.
        # Guarda os itens do catálogo do mercado.
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                categoria TEXT NOT NULL,
                estoque INTEGER NOT NULL DEFAULT 0,
                descricao TEXT DEFAULT ''
            )
            """
        )

        # Tabela de pedidos.
        # Representa a compra associada a um usuário.
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
            """
        )

        # Tabela de itens do pedido.
        # Registra cada produto de um pedido.
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pedido_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                nome_produto TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
            """
        )

        # Confirma a criação das tabelas.
        self.con.commit()

    def hash_senha(self, senha):
        # Gera o hash da senha antes de salvar no banco.
        return hashlib.sha256(senha.encode()).hexdigest()

    def popular_dados_iniciais(self):
        # Usuários padrão para acesso administrativo.
        usuarios_padrao = [
            ("Administrador", "dono", self.hash_senha("admin123"), "dono"),
            ("Funcionário", "funcionario", self.hash_senha("func123"), "funcionario"),
        ]

        # Verifica se os usuários já existem antes de inserir.
        for usuario in usuarios_padrao:
            self.cur.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario[1],))
            if not self.cur.fetchone():
                self.cur.execute(
                    "INSERT INTO usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, ?)",
                    usuario,
                )

        # Adiciona produtos iniciais se o banco estiver vazio.
        self.cur.execute("SELECT COUNT(*) AS total FROM produtos")
        if self.cur.fetchone()["total"] == 0:
            produtos = [
                ("Arroz Premium 5kg", 29.90, "Alimentos", 18, "Pacote premium, ideal para o dia a dia."),
                ("Feijão Carioca 1kg", 8.90, "Alimentos", 26, "Grãos selecionados e alta qualidade."),
                ("Macarrão Espaguete", 5.49, "Alimentos", 34, "Massa tradicional para receitas rápidas."),
                ("Leite Integral 1L", 5.99, "Bebidas", 40, "Leite integral longa vida."),
                ("Refrigerante Cola 2L", 10.99, "Bebidas", 20, "Bebida gelada para toda a família."),
                ("Café Torrado 500g", 16.50, "Alimentos", 15, "Café encorpado e aromático."),
                ("Detergente Neutro", 2.79, "Limpeza", 50, "Limpeza eficiente com alto rendimento."),
                ("Sabão em Pó 1,6kg", 19.90, "Limpeza", 17, "Roupas limpas e perfumadas."),
                ("Papel Higiênico 12 rolos", 18.90, "Higiene", 22, "Folha dupla, macio e resistente."),
                ("Shampoo Hidratante", 15.90, "Higiene", 14, "Cuidado diário para os cabelos."),
            ]
            self.cur.executemany(
                "INSERT INTO produtos (nome, preco, categoria, estoque, descricao) VALUES (?, ?, ?, ?, ?)",
                produtos,
            )

        # Confirma a inserção no banco.
        self.con.commit()

    def autenticar(self, usuario, senha):
        # Converte a senha informada em hash antes da comparação.
        senha_hash = self.hash_senha(senha)

        # Busca um usuário com login e senha compatíveis.
        self.cur.execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND senha = ?",
            (usuario.strip(), senha_hash),
        )
        return self.cur.fetchone()

    def criar_cliente(self, nome, usuario, senha):
        # Cadastra um novo cliente.
        try:
            self.cur.execute(
                "INSERT INTO usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, ?)",
                (nome.strip(), usuario.strip(), self.hash_senha(senha), "cliente"),
            )
            self.con.commit()
            return True, "Conta criada com sucesso!"
        except sqlite3.IntegrityError:
            # Erro comum quando o nome de usuário já existe.
            return False, "Esse nome de usuário já está em uso."

    def buscar_produtos(self, busca="", categoria="Todas"):
        # Monta a consulta base e adiciona filtros quando necessário.
        sql = "SELECT * FROM produtos WHERE 1=1"
        params = []

        # Filtra pelo nome do produto se houver busca.
        if busca.strip():
            sql += " AND lower(nome) LIKE ?"
            params.append(f"%{busca.lower().strip()}%")

        # Filtra por categoria quando a opção não for "Todas".
        if categoria and categoria != "Todas":
            sql += " AND categoria = ?"
            params.append(categoria)

        # Organiza os resultados em ordem alfabética.
        sql += " ORDER BY nome"
        self.cur.execute(sql, tuple(params))
        return self.cur.fetchall()

    def categorias(self):
        # Retorna as categorias existentes sem repetição.
        self.cur.execute("SELECT DISTINCT categoria FROM produtos ORDER BY categoria")
        return [linha[0] for linha in self.cur.fetchall()]

    def adicionar_produto(self, nome, preco, categoria, estoque, descricao):
        # Insere um novo produto no banco.
        self.cur.execute(
            "INSERT INTO produtos (nome, preco, categoria, estoque, descricao) VALUES (?, ?, ?, ?, ?)",
            (nome.strip(), float(preco), categoria.strip(), int(estoque), descricao.strip()),
        )
        self.con.commit()

    def atualizar_produto(self, produto_id, nome, preco, categoria, estoque, descricao):
        # Atualiza os dados do produto selecionado.
        self.cur.execute(
            """
            UPDATE produtos
            SET nome = ?, preco = ?, categoria = ?, estoque = ?, descricao = ?
            WHERE id = ?
            """,
            (nome.strip(), float(preco), categoria.strip(), int(estoque), descricao.strip(), int(produto_id)),
        )
        self.con.commit()

    def remover_produto(self, produto_id):
        # Exclui o produto pelo ID.
        self.cur.execute("DELETE FROM produtos WHERE id = ?", (int(produto_id),))
        self.con.commit()

    def resumo_admin(self):
        # Reúne os indicadores do painel administrativo.

        # Total de produtos cadastrados.
        self.cur.execute("SELECT COUNT(*) AS total FROM produtos")
        total_produtos = self.cur.fetchone()["total"]

        # Total de itens em estoque.
        self.cur.execute("SELECT COALESCE(SUM(estoque), 0) AS total FROM produtos")
        total_estoque = self.cur.fetchone()["total"]

        # Total de pedidos.
        self.cur.execute("SELECT COUNT(*) AS total FROM pedidos")
        total_pedidos = self.cur.fetchone()["total"]

        # Faturamento acumulado.
        self.cur.execute("SELECT COALESCE(SUM(total), 0) AS total FROM pedidos")
        faturamento = self.cur.fetchone()["total"]

        return {
            "produtos": total_produtos,
            "estoque": total_estoque,
            "pedidos": total_pedidos,
            "faturamento": faturamento,
        }

    def criar_pedido(self, usuario_id, itens):
        # Não cria pedido com carrinho vazio.
        if not itens:
            return False, "Carrinho vazio."

        total = 0
        produtos_atualizados = []

        # Valida se todos os produtos existem
        # e se há estoque suficiente para cada item.
        for produto_id, item in itens.items():
            self.cur.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
            produto = self.cur.fetchone()

            if not produto:
                return False, f"Produto ID {produto_id} não encontrado."

            if item["quantidade"] > produto["estoque"]:
                return False, f"Estoque insuficiente para {produto['nome']}."

            subtotal = item["quantidade"] * produto["preco"]
            total += subtotal

            # Guarda os dados já validados para inserir depois.
            produtos_atualizados.append((produto, item["quantidade"], subtotal))

        # Registra a data e hora do pedido.
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Cria o pedido principal.
        self.cur.execute(
            "INSERT INTO pedidos (usuario_id, total, status, criado_em) VALUES (?, ?, ?, ?)",
            (usuario_id, total, "Pago", criado_em),
        )
        pedido_id = self.cur.lastrowid

        # Insere os itens do pedido e atualiza o estoque.
        for produto, quantidade, subtotal in produtos_atualizados:
            self.cur.execute(
                """
                INSERT INTO pedido_itens (pedido_id, produto_id, nome_produto, quantidade, preco_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pedido_id, produto["id"], produto["nome"], quantidade, produto["preco"], subtotal),
            )
            self.cur.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (quantidade, produto["id"]),
            )

        self.con.commit()
        return True, f"Pedido #{pedido_id} finalizado com sucesso!"

    def pedidos_cliente(self, usuario_id):
        # Retorna os pedidos do cliente do mais recente para o mais antigo.
        self.cur.execute(
            "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id DESC",
            (usuario_id,),
        )
        return self.cur.fetchall()

    def pedidos_gerais(self):
        # Lista todos os pedidos com os dados do usuário.
        self.cur.execute(
            """
            SELECT pedidos.id, usuarios.nome, usuarios.usuario, pedidos.total, pedidos.status, pedidos.criado_em
            FROM pedidos
            INNER JOIN usuarios ON usuarios.id = pedidos.usuario_id
            ORDER BY pedidos.id DESC
            """
        )
        return self.cur.fetchall()

    def itens_pedido(self, pedido_id):
        # Retorna os itens de um pedido específico.
        self.cur.execute(
            "SELECT * FROM pedido_itens WHERE pedido_id = ? ORDER BY id",
            (pedido_id,),
        )
        return self.cur.fetchall()

    def fechar(self):
        # Fecha a conexão com o banco ao encerrar.
        self.con.close()


# Classe da interface gráfica e do fluxo da aplicação.
class MercadoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mercado Fácil Pro")
        self.root.geometry("1280x760")
        self.root.minsize(1120, 700)
        self.root.configure(bg="#0f172a")

        # Inicia o banco logo no começo.
        self.db = BancoMercado()

        # Usuário logado no momento.
        self.usuario_atual = None

        # Carrinho em memória durante a sessão.
        self.carrinho = {}

        # Guarda o ID do produto selecionado no painel admin.
        self.produto_selecionado_id = None

        # Paleta de cores da interface.
        self.cores = {
            "bg": "#0f172a",
            "bg_sec": "#111827",
            "painel": "#1e293b",
            "painel_claro": "#334155",
            "card": "#ffffff",
            "texto": "#e2e8f0",
            "texto_escuro": "#0f172a",
            "muted": "#94a3b8",
            "primaria": "#22c55e",
            "primaria_hover": "#16a34a",
            "secundaria": "#38bdf8",
            "aviso": "#f59e0b",
            "perigo": "#ef4444",
            "borda": "#cbd5e1",
            "fundo_card_produto": "#f8fafc",
        }

        # Aplica os estilos visuais do ttk.
        self.estilizar_ttk()

        # Define o comportamento do botão de fechar.
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        # Inicia exibindo a tela principal.
        self.tela_inicial()

    def estilizar_ttk(self):
        # Configura os estilos visuais dos componentes ttk.
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(
            "Card.TFrame",
            background=self.cores["card"],
            relief="flat",
        )
        self.style.configure(
            "Dark.TFrame",
            background=self.cores["painel"],
        )
        self.style.configure(
            "App.TLabel",
            background=self.cores["bg"],
            foreground=self.cores["texto"],
            font=("Segoe UI", 11),
        )
        self.style.configure(
            "Title.TLabel",
            background=self.cores["bg"],
            foreground="white",
            font=("Segoe UI", 28, "bold"),
        )
        self.style.configure(
            "Subtitle.TLabel",
            background=self.cores["bg"],
            foreground=self.cores["muted"],
            font=("Segoe UI", 11),
        )
        self.style.configure(
            "PanelTitle.TLabel",
            background=self.cores["card"],
            foreground=self.cores["texto_escuro"],
            font=("Segoe UI", 16, "bold"),
        )
        self.style.configure(
            "PanelText.TLabel",
            background=self.cores["card"],
            foreground="#475569",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="white",
            background=self.cores["primaria"],
            borderwidth=0,
            focusthickness=0,
            padding=(14, 10),
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", self.cores["primaria_hover"])],
        )
        self.style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="white",
            background=self.cores["secundaria"],
            borderwidth=0,
            padding=(12, 10),
        )
        self.style.map(
            "Secondary.TButton",
            background=[("active", "#0ea5e9")],
        )
        self.style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="white",
            background=self.cores["perigo"],
            borderwidth=0,
            padding=(12, 10),
        )
        self.style.map(
            "Danger.TButton",
            background=[("active", "#dc2626")],
        )
        self.style.configure(
            "Modern.Treeview",
            rowheight=32,
            font=("Segoe UI", 10),
            background="white",
            fieldbackground="white",
            foreground="#111827",
            bordercolor=self.cores["borda"],
        )
        self.style.configure(
            "Modern.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#e2e8f0",
            foreground="#0f172a",
        )
        self.style.map(
            "Modern.Treeview",
            background=[("selected", "#dcfce7")],
            foreground=[("selected", "#14532d")],
        )
        self.style.configure(
            "TNotebook",
            background=self.cores["bg_sec"],
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
        )

    def limpar_janela(self):
        # Limpa os widgets antes de montar a nova tela.
        for widget in self.root.winfo_children():
            widget.destroy()

    def titulo_secao(self, parent, titulo, subtitulo, dark=False):
        # Padroniza títulos e subtítulos das seções.
        bg = self.cores["painel"] if dark else self.cores["card"]
        fg_titulo = "white" if dark else self.cores["texto_escuro"]
        fg_subtitulo = self.cores["muted"] if dark else "#64748b"

        tk.Label(
            parent,
            text=titulo,
            bg=bg,
            fg=fg_titulo,
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        tk.Label(
            parent,
            text=subtitulo,
            bg=bg,
            fg=fg_subtitulo,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

    def criar_entry(self, parent, label, show=None):
        # Cria um campo com rótulo e estilo padrão.
        wrapper = tk.Frame(parent, bg=self.cores["card"])
        wrapper.pack(fill="x", pady=8)

        tk.Label(
            wrapper,
            text=label,
            bg=self.cores["card"],
            fg="#334155",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        entry = tk.Entry(
            wrapper,
            show=show,
            relief="flat",
            bg="#f8fafc",
            fg="#0f172a",
            insertbackground="#0f172a",
            font=("Segoe UI", 11),
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor=self.cores["secundaria"],
            bd=0,
        )
        entry.pack(fill="x", ipady=10)
        return entry

    def criar_cartao_info(self, parent, titulo, valor, cor):
        # Card de resumo do painel administrativo.
        card = tk.Frame(parent, bg=self.cores["card"], padx=18, pady=16, highlightthickness=1, highlightbackground="#e2e8f0")
        card.pack(side="left", fill="both", expand=True, padx=8)

        tk.Label(card, text=titulo, bg=self.cores["card"], fg="#64748b", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(card, text=valor, bg=self.cores["card"], fg=cor, font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(8, 0))
        return card

    def tela_inicial(self):
        # Monta a tela inicial com login e cadastro.
        self.limpar_janela()

        principal = tk.Frame(self.root, bg=self.cores["bg"])
        principal.pack(fill="both", expand=True)

        esquerda = tk.Frame(principal, bg=self.cores["bg"], padx=50, pady=40)
        esquerda.pack(side="left", fill="both", expand=True)

        direita = tk.Frame(principal, bg=self.cores["bg_sec"], width=470, padx=28, pady=28)
        direita.pack(side="right", fill="y")
        direita.pack_propagate(False)

        tk.Label(
            esquerda,
            text="Mercado Fácil Pro",
            bg=self.cores["bg"],
            fg="white",
            font=("Segoe UI", 34, "bold"),
        ).pack(anchor="w", pady=(30, 8))

        tk.Label(
            esquerda,
            text="Um sistema de mercado com visual mais moderno, fluxo real de compra e áreas separadas para clientes e equipe administrativa.",
            bg=self.cores["bg"],
            fg=self.cores["muted"],
            justify="left",
            wraplength=560,
            font=("Segoe UI", 13),
        ).pack(anchor="w")

        # Blocos com os recursos do sistema.
        destaques = tk.Frame(esquerda, bg=self.cores["bg"])
        destaques.pack(anchor="w", pady=40)

        for titulo, descricao in [
            ("Login por perfil", "Acesso automático para dono, funcionário ou cliente."),
            ("Catálogo elegante", "Busca, filtro por categoria e cards de produto mais bonitos."),
            ("Pedidos organizados", "Clientes acompanham compras e admins controlam produtos."),
        ]:
            bloco = tk.Frame(destaques, bg=self.cores["painel"], padx=20, pady=18)
            bloco.pack(fill="x", pady=8)
            tk.Label(bloco, text=titulo, bg=self.cores["painel"], fg="white", font=("Segoe UI", 14, "bold")).pack(anchor="w")
            tk.Label(bloco, text=descricao, bg=self.cores["painel"], fg=self.cores["muted"], font=("Segoe UI", 10), justify="left", wraplength=460).pack(anchor="w", pady=(6, 0))

        # Exibe as credenciais iniciais dos perfis administrativos.
        credenciais = tk.Frame(esquerda, bg=self.cores["bg"])
        credenciais.pack(anchor="w", pady=(20, 0))
        tk.Label(credenciais, text="Acessos iniciais de administrador", bg=self.cores["bg"], fg="#86efac", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(credenciais, text="Dono: dono / admin123", bg=self.cores["bg"], fg="white", font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 0))
        tk.Label(credenciais, text="Funcionário: funcionario / func123", bg=self.cores["bg"], fg="white", font=("Segoe UI", 11)).pack(anchor="w")

        # Área de login.
        card_login = tk.Frame(direita, bg=self.cores["card"], padx=24, pady=22)
        card_login.pack(fill="x")
        self.titulo_secao(card_login, "Entrar no sistema", "Use a mesma tela para clientes e administradores.")
        self.login_usuario = self.criar_entry(card_login, "Usuário")
        self.login_senha = self.criar_entry(card_login, "Senha", show="*")
        ttk.Button(card_login, text="Entrar agora", style="Primary.TButton", command=self.realizar_login).pack(fill="x", pady=(16, 0))

        separador = tk.Frame(direita, bg=self.cores["bg_sec"], height=16)
        separador.pack(fill="x")

        # Área de cadastro de cliente.
        card_cadastro = tk.Frame(direita, bg=self.cores["card"], padx=24, pady=22)
        card_cadastro.pack(fill="x")
        self.titulo_secao(card_cadastro, "Criar conta de cliente", "Clientes podem se cadastrar para comprar e acompanhar pedidos.")
        self.cad_nome = self.criar_entry(card_cadastro, "Nome completo")
        self.cad_usuario = self.criar_entry(card_cadastro, "Usuário")
        self.cad_senha = self.criar_entry(card_cadastro, "Senha", show="*")
        ttk.Button(card_cadastro, text="Criar conta", style="Secondary.TButton", command=self.criar_conta_cliente).pack(fill="x", pady=(16, 0))

    def realizar_login(self):
        # Recupera os dados digitados.
        usuario = self.login_usuario.get().strip()
        senha = self.login_senha.get().strip()

        # Faz uma validação básica antes da consulta.
        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Preencha usuário e senha.")
            return

        # Tenta autenticar no banco.
        registro = self.db.autenticar(usuario, senha)
        if not registro:
            messagebox.showerror("Login", "Usuário ou senha inválidos.")
            return

        # Se autenticar, guarda os dados do usuário e redireciona pelo perfil.
        self.usuario_atual = registro
        self.carrinho = {}

        if registro["perfil"] in ("dono", "funcionario"):
            self.tela_admin()
        else:
            self.tela_cliente()

    def criar_conta_cliente(self):
        # Recupera os dados do formulário de cadastro.
        nome = self.cad_nome.get().strip()
        usuario = self.cad_usuario.get().strip()
        senha = self.cad_senha.get().strip()

        # Valida se todos os campos foram preenchidos.
        if not nome or not usuario or not senha:
            messagebox.showwarning("Cadastro", "Preencha todos os campos para criar a conta.")
            return

        # Tenta criar a conta do cliente.
        sucesso, mensagem = self.db.criar_cliente(nome, usuario, senha)
        if sucesso:
            messagebox.showinfo("Cadastro", mensagem)

            # Se der certo, limpa o formulário.
            self.cad_nome.delete(0, tk.END)
            self.cad_usuario.delete(0, tk.END)
            self.cad_senha.delete(0, tk.END)
        else:
            messagebox.showerror("Cadastro", mensagem)

    def topo_aplicacao(self, titulo, subtitulo):
        # Topo padrão das telas internas.
        topo = tk.Frame(self.root, bg=self.cores["bg_sec"], padx=28, pady=16)
        topo.pack(fill="x")

        info = tk.Frame(topo, bg=self.cores["bg_sec"])
        info.pack(side="left")
        tk.Label(info, text=titulo, bg=self.cores["bg_sec"], fg="white", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(info, text=subtitulo, bg=self.cores["bg_sec"], fg=self.cores["muted"], font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        acoes = tk.Frame(topo, bg=self.cores["bg_sec"])
        acoes.pack(side="right")
        ttk.Button(acoes, text="Sair", style="Danger.TButton", command=self.logout).pack(side="right")

    def logout(self):
        # Ao sair, limpa a sessão e volta para a tela inicial.
        self.usuario_atual = None
        self.carrinho = {}
        self.produto_selecionado_id = None
        self.tela_inicial()

    def tela_admin(self):
        # Tela principal do administrador e do funcionário.
        self.limpar_janela()

        nome = self.usuario_atual["nome"]
        perfil = self.usuario_atual["perfil"].capitalize()

        self.topo_aplicacao(
            f"Painel administrativo • {perfil}",
            f"Bem-vindo, {nome}. Gerencie catálogo, estoque e pedidos em um só lugar.",
        )

        corpo = tk.Frame(self.root, bg=self.cores["bg"], padx=24, pady=20)
        corpo.pack(fill="both", expand=True)

        # Exibe os indicadores gerais no topo.
        resumo = self.db.resumo_admin()
        linha_cards = tk.Frame(corpo, bg=self.cores["bg"])
        linha_cards.pack(fill="x", pady=(0, 16))
        self.criar_cartao_info(linha_cards, "Produtos cadastrados", str(resumo["produtos"]), self.cores["secundaria"])
        self.criar_cartao_info(linha_cards, "Itens em estoque", str(resumo["estoque"]), self.cores["primaria"])
        self.criar_cartao_info(linha_cards, "Pedidos realizados", str(resumo["pedidos"]), self.cores["aviso"])
        self.criar_cartao_info(linha_cards, "Faturamento", f"R$ {resumo['faturamento']:.2f}", self.cores["perigo"])

        area = tk.Frame(corpo, bg=self.cores["bg"])
        area.pack(fill="both", expand=True)

        # Lado esquerdo: formulário de produtos.
        lateral = tk.Frame(area, bg=self.cores["card"], padx=20, pady=20, highlightthickness=1, highlightbackground="#dbeafe")
        lateral.pack(side="left", fill="y", padx=(0, 16))
        lateral.configure(width=350)
        lateral.pack_propagate(False)

        self.titulo_secao(lateral, "Cadastro de produtos", "Adicione novos itens ou atualize os já existentes.")
        self.admin_nome = self.criar_entry(lateral, "Nome do produto")
        self.admin_preco = self.criar_entry(lateral, "Preço")
        self.admin_categoria = self.criar_entry(lateral, "Categoria")
        self.admin_estoque = self.criar_entry(lateral, "Estoque")

        tk.Label(lateral, text="Descrição", bg=self.cores["card"], fg="#334155", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 4))
        self.admin_descricao = tk.Text(
            lateral,
            height=5,
            relief="flat",
            bg="#f8fafc",
            fg="#0f172a",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor=self.cores["secundaria"],
        )
        self.admin_descricao.pack(fill="x")

        # Botões de ações administrativas.
        botoes = tk.Frame(lateral, bg=self.cores["card"])
        botoes.pack(fill="x", pady=16)
        ttk.Button(botoes, text="Novo produto", style="Primary.TButton", command=self.salvar_novo_produto).pack(fill="x", pady=4)
        ttk.Button(botoes, text="Atualizar selecionado", style="Secondary.TButton", command=self.atualizar_produto_admin).pack(fill="x", pady=4)
        ttk.Button(botoes, text="Remover selecionado", style="Danger.TButton", command=self.remover_produto_admin).pack(fill="x", pady=4)
        ttk.Button(botoes, text="Limpar formulário", command=self.limpar_formulario_produto).pack(fill="x", pady=4)

        # Lado direito: abas de produtos e pedidos.
        painel = tk.Frame(area, bg=self.cores["bg"])
        painel.pack(side="left", fill="both", expand=True)

        abas = ttk.Notebook(painel)
        abas.pack(fill="both", expand=True)

        aba_produtos = tk.Frame(abas, bg=self.cores["card"])
        aba_pedidos = tk.Frame(abas, bg=self.cores["card"])
        abas.add(aba_produtos, text="Produtos")
        abas.add(aba_pedidos, text="Pedidos")

        self.montar_tabela_produtos_admin(aba_produtos)
        self.montar_tabela_pedidos_admin(aba_pedidos)
        self.carregar_tabela_produtos_admin()
        self.carregar_tabela_pedidos_admin()

    def montar_tabela_produtos_admin(self, parent):
        # Monta a tabela de produtos do administrador.
        topo = tk.Frame(parent, bg=self.cores["card"], padx=18, pady=18)
        topo.pack(fill="x")
        self.titulo_secao(topo, "Lista de produtos", "Selecione um item para editar os dados.")

        tabela_frame = tk.Frame(parent, bg=self.cores["card"], padx=18, pady=0)
        tabela_frame.pack(fill="both", expand=True)

        colunas = ("id", "nome", "categoria", "preco", "estoque")
        self.tree_produtos = ttk.Treeview(tabela_frame, columns=colunas, show="headings", style="Modern.Treeview")

        for col, largura in [("id", 60), ("nome", 290), ("categoria", 150), ("preco", 110), ("estoque", 100)]:
            self.tree_produtos.heading(col, text=col.upper())
            self.tree_produtos.column(col, width=largura, anchor="center")

        self.tree_produtos.column("nome", anchor="w")
        self.tree_produtos.pack(side="left", fill="both", expand=True)

        # Preenche o formulário quando um item é selecionado.
        self.tree_produtos.bind("<<TreeviewSelect>>", self.selecionar_produto_admin)

        barra = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")

    def montar_tabela_pedidos_admin(self, parent):
        # Monta a tabela de pedidos do painel administrativo.
        topo = tk.Frame(parent, bg=self.cores["card"], padx=18, pady=18)
        topo.pack(fill="x")
        self.titulo_secao(topo, "Pedidos dos clientes", "Visualize as compras finalizadas e os detalhes de cada pedido.")

        tabela_frame = tk.Frame(parent, bg=self.cores["card"], padx=18)
        tabela_frame.pack(fill="both", expand=True)

        colunas = ("id", "cliente", "usuario", "total", "status", "data")
        self.tree_pedidos = ttk.Treeview(tabela_frame, columns=colunas, show="headings", style="Modern.Treeview")

        definicoes = {
            "id": 70,
            "cliente": 220,
            "usuario": 140,
            "total": 100,
            "status": 100,
            "data": 140,
        }

        for col in colunas:
            self.tree_pedidos.heading(col, text=col.upper())
            self.tree_pedidos.column(col, width=definicoes[col], anchor="center")

        self.tree_pedidos.column("cliente", anchor="w")
        self.tree_pedidos.pack(side="left", fill="both", expand=True)

        barra = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree_pedidos.yview)
        self.tree_pedidos.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")

        rodape = tk.Frame(parent, bg=self.cores["card"], padx=18, pady=16)
        rodape.pack(fill="x")
        ttk.Button(rodape, text="Ver itens do pedido", style="Secondary.TButton", command=self.ver_itens_pedido_admin).pack(anchor="e")

    def carregar_tabela_produtos_admin(self):
        # Limpa a tabela atual.
        for item in self.tree_produtos.get_children():
            self.tree_produtos.delete(item)

        # Recarrega os produtos do banco.
        for produto in self.db.buscar_produtos():
            self.tree_produtos.insert(
                "",
                tk.END,
                values=(
                    produto["id"],
                    produto["nome"],
                    produto["categoria"],
                    f"R$ {produto['preco']:.2f}",
                    produto["estoque"],
                ),
            )

    def carregar_tabela_pedidos_admin(self):
        # Limpa a tabela atual antes de recarregar.
        for item in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(item)

        # Insere os pedidos encontrados no banco.
        for pedido in self.db.pedidos_gerais():
            self.tree_pedidos.insert(
                "",
                tk.END,
                values=(
                    pedido["id"],
                    pedido["nome"],
                    pedido["usuario"],
                    f"R$ {pedido['total']:.2f}",
                    pedido["status"],
                    pedido["criado_em"],
                ),
            )

    def selecionar_produto_admin(self, _evento=None):
        # Recupera o item selecionado na tabela.
        selecionado = self.tree_produtos.selection()
        if not selecionado:
            return

        valores = self.tree_produtos.item(selecionado[0], "values")
        produto_id = int(valores[0])

        # Busca os dados completos do produto.
        produto = next((p for p in self.db.buscar_produtos() if p["id"] == produto_id), None)
        if not produto:
            return

        # Guarda o ID e preenche o formulário com os dados do item.
        self.produto_selecionado_id = produto_id
        self.admin_nome.delete(0, tk.END)
        self.admin_nome.insert(0, produto["nome"])
        self.admin_preco.delete(0, tk.END)
        self.admin_preco.insert(0, str(produto["preco"]))
        self.admin_categoria.delete(0, tk.END)
        self.admin_categoria.insert(0, produto["categoria"])
        self.admin_estoque.delete(0, tk.END)
        self.admin_estoque.insert(0, str(produto["estoque"]))
        self.admin_descricao.delete("1.0", tk.END)
        self.admin_descricao.insert("1.0", produto["descricao"])

    def validar_form_produto(self):
        # Lê e trata os dados digitados no formulário.
        nome = self.admin_nome.get().strip()
        preco = self.admin_preco.get().strip().replace(",", ".")
        categoria = self.admin_categoria.get().strip()
        estoque = self.admin_estoque.get().strip()
        descricao = self.admin_descricao.get("1.0", tk.END).strip()

        # Validação básica de preenchimento.
        if not nome or not preco or not categoria or not estoque:
            raise ValueError("Preencha nome, preço, categoria e estoque.")

        # Validação de valores numéricos.
        try:
            preco = float(preco)
            estoque = int(estoque)
        except ValueError:
            raise ValueError("Preço ou estoque em formato inválido.")

        # Não permite valores negativos.
        if preco < 0 or estoque < 0:
            raise ValueError("Preço e estoque devem ser maiores ou iguais a zero.")

        return nome, preco, categoria, estoque, descricao

    def salvar_novo_produto(self):
        # Cadastra um novo produto.
        try:
            nome, preco, categoria, estoque, descricao = self.validar_form_produto()
            self.db.adicionar_produto(nome, preco, categoria, estoque, descricao)
            self.limpar_formulario_produto()
            self.tela_admin()
            messagebox.showinfo("Produto", "Produto cadastrado com sucesso.")
        except Exception as erro:
            messagebox.showerror("Produto", str(erro))

    def atualizar_produto_admin(self):
        # Atualiza o produto selecionado.
        if not self.produto_selecionado_id:
            messagebox.showwarning("Produto", "Selecione um produto para atualizar.")
            return

        try:
            nome, preco, categoria, estoque, descricao = self.validar_form_produto()
            self.db.atualizar_produto(self.produto_selecionado_id, nome, preco, categoria, estoque, descricao)
            self.limpar_formulario_produto()
            self.tela_admin()
            messagebox.showinfo("Produto", "Produto atualizado com sucesso.")
        except Exception as erro:
            messagebox.showerror("Produto", str(erro))

    def remover_produto_admin(self):
        # Remove o produto selecionado.
        if not self.produto_selecionado_id:
            messagebox.showwarning("Produto", "Selecione um produto para remover.")
            return

        confirmar = messagebox.askyesno("Excluir", "Deseja remover o produto selecionado?")
        if confirmar:
            self.db.remover_produto(self.produto_selecionado_id)
            self.limpar_formulario_produto()
            self.tela_admin()
            messagebox.showinfo("Produto", "Produto removido com sucesso.")

    def limpar_formulario_produto(self):
        # Limpa o formulário de cadastro e edição.
        self.produto_selecionado_id = None

        for entry in [self.admin_nome, self.admin_preco, self.admin_categoria, self.admin_estoque]:
            entry.delete(0, tk.END)

        self.admin_descricao.delete("1.0", tk.END)

    def ver_itens_pedido_admin(self):
        # Exibe os itens do pedido em uma janela separada.
        selecionado = self.tree_pedidos.selection()
        if not selecionado:
            messagebox.showwarning("Pedidos", "Selecione um pedido para visualizar os itens.")
            return

        pedido_id = int(self.tree_pedidos.item(selecionado[0], "values")[0])
        itens = self.db.itens_pedido(pedido_id)

        if not itens:
            messagebox.showinfo("Pedidos", "Esse pedido não possui itens.")
            return

        janela = tk.Toplevel(self.root)
        janela.title(f"Itens do pedido #{pedido_id}")
        janela.geometry("620x380")
        janela.configure(bg=self.cores["bg_sec"])

        tk.Label(janela, text=f"Pedido #{pedido_id}", bg=self.cores["bg_sec"], fg="white", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=(20, 4))
        tk.Label(janela, text="Detalhes dos produtos comprados", bg=self.cores["bg_sec"], fg=self.cores["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=20)

        caixa = tk.Frame(janela, bg="white", padx=16, pady=16)
        caixa.pack(fill="both", expand=True, padx=20, pady=20)

        for item in itens:
            texto = f"• {item['nome_produto']}  |  Qtd: {item['quantidade']}  |  Unit.: R$ {item['preco_unitario']:.2f}  |  Subtotal: R$ {item['subtotal']:.2f}"
            tk.Label(caixa, text=texto, bg="white", fg="#0f172a", anchor="w", justify="left", font=("Segoe UI", 10)).pack(fill="x", pady=6)

    def tela_cliente(self):
        # Tela principal do cliente.
        self.limpar_janela()
        nome = self.usuario_atual["nome"]

        self.topo_aplicacao(
            "Área do cliente",
            f"Olá, {nome}. Explore os produtos, monte o carrinho e acompanhe seus pedidos.",
        )

        corpo = tk.Frame(self.root, bg=self.cores["bg"], padx=24, pady=20)
        corpo.pack(fill="both", expand=True)

        # Barra superior com busca, filtro e ações.
        barra = tk.Frame(corpo, bg=self.cores["bg"])
        barra.pack(fill="x", pady=(0, 14))

        busca_box = tk.Frame(barra, bg=self.cores["card"], padx=14, pady=12)
        busca_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(busca_box, text="Buscar produto", bg=self.cores["card"], fg="#334155", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self.busca_cliente = tk.Entry(busca_box, relief="flat", bg="#f8fafc", font=("Segoe UI", 11), highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor=self.cores["secundaria"])
        self.busca_cliente.pack(fill="x", ipady=8, pady=(6, 0))

        # Atualiza o catálogo a cada tecla.
        self.busca_cliente.bind("<KeyRelease>", lambda _e: self.carregar_catalogo_cliente())

        filtro_box = tk.Frame(barra, bg=self.cores["card"], padx=14, pady=12)
        filtro_box.pack(side="left", padx=(0, 12))
        tk.Label(filtro_box, text="Categoria", bg=self.cores["card"], fg="#334155", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        categorias = ["Todas"] + self.db.categorias()
        self.combo_categoria = ttk.Combobox(filtro_box, values=categorias, state="readonly", width=18)
        self.combo_categoria.current(0)
        self.combo_categoria.pack(ipady=4, pady=(6, 0))

        # Atualiza o catálogo quando a categoria mudar.
        self.combo_categoria.bind("<<ComboboxSelected>>", lambda _e: self.carregar_catalogo_cliente())

        acoes = tk.Frame(barra, bg=self.cores["bg"])
        acoes.pack(side="right")
        ttk.Button(acoes, text="Meus pedidos", style="Secondary.TButton", command=self.mostrar_pedidos_cliente).pack(side="right", padx=(8, 0))
        ttk.Button(acoes, text="Finalizar compra", style="Primary.TButton", command=self.finalizar_compra).pack(side="right")

        conteudo = tk.Frame(corpo, bg=self.cores["bg"])
        conteudo.pack(fill="both", expand=True)

        # Lado esquerdo: catálogo.
        self.area_catalogo = tk.Frame(conteudo, bg=self.cores["bg"])
        self.area_catalogo.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # Lado direito: carrinho.
        self.area_carrinho = tk.Frame(conteudo, bg=self.cores["card"], width=330, padx=18, pady=18, highlightthickness=1, highlightbackground="#dbeafe")
        self.area_carrinho.pack(side="right", fill="y")
        self.area_carrinho.pack_propagate(False)

        self.construir_catalogo_scrollavel()
        self.atualizar_painel_carrinho()
        self.carregar_catalogo_cliente()

    def construir_catalogo_scrollavel(self):
        # Cria uma área com canvas e scrollbar para o catálogo.
        wrapper = tk.Frame(self.area_catalogo, bg=self.cores["bg"])
        wrapper.pack(fill="both", expand=True)

        self.canvas_catalogo = tk.Canvas(wrapper, bg=self.cores["bg"], highlightthickness=0)
        barra = ttk.Scrollbar(wrapper, orient="vertical", command=self.canvas_catalogo.yview)
        self.canvas_catalogo.configure(yscrollcommand=barra.set)

        self.frame_cards = tk.Frame(self.canvas_catalogo, bg=self.cores["bg"])
        self.frame_cards.bind(
            "<Configure>",
            lambda e: self.canvas_catalogo.configure(scrollregion=self.canvas_catalogo.bbox("all")),
        )

        self.canvas_catalogo.create_window((0, 0), window=self.frame_cards, anchor="nw")
        self.canvas_catalogo.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def carregar_catalogo_cliente(self):
        # Limpa os cards antes de recarregar o catálogo.
        for widget in self.frame_cards.winfo_children():
            widget.destroy()

        # Recupera a busca e o filtro atuais.
        busca = self.busca_cliente.get().strip() if hasattr(self, "busca_cliente") else ""
        categoria = self.combo_categoria.get() if hasattr(self, "combo_categoria") else "Todas"

        # Consulta os produtos no banco.
        produtos = self.db.buscar_produtos(busca, categoria)

        # Exibe uma mensagem se nenhum produto for encontrado.
        if not produtos:
            vazio = tk.Frame(self.frame_cards, bg=self.cores["card"], padx=30, pady=30)
            vazio.pack(fill="x", pady=20)
            tk.Label(vazio, text="Nenhum produto encontrado", bg=self.cores["card"], fg="#0f172a", font=("Segoe UI", 16, "bold")).pack()
            tk.Label(vazio, text="Tente outro termo de busca ou selecione uma categoria diferente.", bg=self.cores["card"], fg="#64748b", font=("Segoe UI", 10)).pack(pady=(8, 0))
            return

        # Distribui os produtos em duas colunas.
        for indice, produto in enumerate(produtos):
            linha = indice // 2
            coluna = indice % 2
            self.criar_card_produto(self.frame_cards, produto, linha, coluna)

        for col in range(2):
            self.frame_cards.grid_columnconfigure(col, weight=1)

    def criar_card_produto(self, parent, produto, linha, coluna):
        # Card de cada produto no catálogo.
        card = tk.Frame(
            parent,
            bg=self.cores["fundo_card_produto"],
            padx=18,
            pady=18,
            highlightthickness=1,
            highlightbackground="#dbeafe",
        )
        card.grid(row=linha, column=coluna, padx=10, pady=10, sticky="nsew")

        topo = tk.Frame(card, bg=self.cores["fundo_card_produto"])
        topo.pack(fill="x")

        tk.Label(topo, text=produto["categoria"], bg="#dbeafe", fg="#1d4ed8", font=("Segoe UI", 9, "bold"), padx=10, pady=4).pack(side="left")

        # A cor do estoque muda conforme a disponibilidade.
        estoque_cor = self.cores["primaria"] if produto["estoque"] > 0 else self.cores["perigo"]
        tk.Label(topo, text=f"Estoque: {produto['estoque']}", bg=self.cores["fundo_card_produto"], fg=estoque_cor, font=("Segoe UI", 9, "bold")).pack(side="right")

        tk.Label(card, text=produto["nome"], bg=self.cores["fundo_card_produto"], fg="#0f172a", font=("Segoe UI", 16, "bold"), wraplength=340, justify="left").pack(anchor="w", pady=(14, 6))
        tk.Label(card, text=produto["descricao"], bg=self.cores["fundo_card_produto"], fg="#64748b", font=("Segoe UI", 10), wraplength=340, justify="left").pack(anchor="w")
        tk.Label(card, text=f"R$ {produto['preco']:.2f}", bg=self.cores["fundo_card_produto"], fg="#059669", font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(12, 10))

        rodape = tk.Frame(card, bg=self.cores["fundo_card_produto"])
        rodape.pack(fill="x")

        # Variável da quantidade desejada.
        quantidade = tk.IntVar(value=1)

        spin = tk.Spinbox(
            rodape,
            from_=1,
            to=max(1, produto["estoque"]),
            textvariable=quantidade,
            width=5,
            font=("Segoe UI", 10),
            justify="center",
            relief="flat",
            bg="white",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
        )
        spin.pack(side="left")

        botao = tk.Button(
            rodape,
            text="Adicionar ao carrinho",
            bg=self.cores["primaria"],
            fg="white",
            activebackground=self.cores["primaria_hover"],
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            command=lambda p=produto, q=quantidade: self.adicionar_carrinho(p, q.get()),
        )
        botao.pack(side="right")

        # Desabilita os controles se o produto estiver sem estoque.
        if produto["estoque"] == 0:
            spin.config(state="disabled")
            botao.config(state="disabled", bg="#94a3b8")

    def adicionar_carrinho(self, produto, quantidade):
        # Converte a quantidade para inteiro.
        try:
            quantidade = int(quantidade)
        except ValueError:
            quantidade = 1

        # Não aceita quantidades menores ou iguais a zero.
        if quantidade <= 0:
            messagebox.showwarning("Carrinho", "A quantidade deve ser maior que zero.")
            return

        # Não deixa ultrapassar o estoque do produto.
        if quantidade > produto["estoque"]:
            messagebox.showerror("Carrinho", "Quantidade maior que o estoque disponível.")
            return

        produto_id = produto["id"]
        qtd_atual = self.carrinho.get(produto_id, {}).get("quantidade", 0)

        # Se o item já estiver no carrinho, valida a soma das quantidades.
        if qtd_atual + quantidade > produto["estoque"]:
            messagebox.showerror("Carrinho", "A soma no carrinho ultrapassa o estoque disponível.")
            return

        # Registra o item no carrinho em memória.
        self.carrinho[produto_id] = {
            "produto": produto,
            "quantidade": qtd_atual + quantidade,
        }

        self.atualizar_painel_carrinho()
        messagebox.showinfo("Carrinho", f"{produto['nome']} adicionado ao carrinho.")

    def atualizar_painel_carrinho(self):
        # Limpa o painel antes de redesenhar o estado atual.
        for widget in self.area_carrinho.winfo_children():
            widget.destroy()

        self.titulo_secao(self.area_carrinho, "Seu carrinho", "Revise os itens antes de finalizar a compra.")

        # Exibe uma mensagem se o carrinho estiver vazio.
        if not self.carrinho:
            vazio = tk.Frame(self.area_carrinho, bg="#f8fafc", padx=18, pady=18)
            vazio.pack(fill="x", pady=18)
            tk.Label(vazio, text="Carrinho vazio", bg="#f8fafc", fg="#0f172a", font=("Segoe UI", 14, "bold")).pack(anchor="w")
            tk.Label(vazio, text="Adicione produtos do catálogo para começar sua compra.", bg="#f8fafc", fg="#64748b", font=("Segoe UI", 10), wraplength=250, justify="left").pack(anchor="w", pady=(6, 0))
        else:
            total = 0

            # Monta um bloco visual para cada item do carrinho.
            for produto_id, item in self.carrinho.items():
                produto = item["produto"]
                quantidade = item["quantidade"]
                subtotal = produto["preco"] * quantidade
                total += subtotal

                bloco = tk.Frame(self.area_carrinho, bg="#f8fafc", padx=12, pady=12, highlightthickness=1, highlightbackground="#e2e8f0")
                bloco.pack(fill="x", pady=6)
                tk.Label(bloco, text=produto["nome"], bg="#f8fafc", fg="#0f172a", font=("Segoe UI", 11, "bold"), wraplength=250, justify="left").pack(anchor="w")
                tk.Label(bloco, text=f"Qtd: {quantidade}  •  Subtotal: R$ {subtotal:.2f}", bg="#f8fafc", fg="#475569", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

                tk.Button(
                    bloco,
                    text="Remover",
                    bg="#fee2e2",
                    fg="#b91c1c",
                    relief="flat",
                    font=("Segoe UI", 9, "bold"),
                    command=lambda pid=produto_id: self.remover_do_carrinho(pid),
                ).pack(anchor="e", pady=(8, 0))

            # Resumo final do carrinho.
            resumo = tk.Frame(self.area_carrinho, bg=self.cores["card"], pady=12)
            resumo.pack(fill="x", pady=(12, 0))
            tk.Label(resumo, text=f"Total: R$ {total:.2f}", bg=self.cores["card"], fg="#059669", font=("Segoe UI", 20, "bold")).pack(anchor="w")
            tk.Label(resumo, text=f"Itens: {sum(item['quantidade'] for item in self.carrinho.values())}", bg=self.cores["card"], fg="#64748b", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        # Botões principais do carrinho.
        ttk.Button(self.area_carrinho, text="Finalizar compra", style="Primary.TButton", command=self.finalizar_compra).pack(fill="x", pady=(18, 8))
        ttk.Button(self.area_carrinho, text="Ver meus pedidos", style="Secondary.TButton", command=self.mostrar_pedidos_cliente).pack(fill="x")

    def remover_do_carrinho(self, produto_id):
        # Remove um item do carrinho.
        if produto_id in self.carrinho:
            del self.carrinho[produto_id]
            self.atualizar_painel_carrinho()

    def finalizar_compra(self):
        # Não finaliza se o carrinho estiver vazio.
        if not self.carrinho:
            messagebox.showwarning("Compra", "Seu carrinho está vazio.")
            return

        # Converte o carrinho para o formato esperado pelo banco.
        itens = {produto_id: {"quantidade": item["quantidade"]} for produto_id, item in self.carrinho.items()}

        sucesso, mensagem = self.db.criar_pedido(self.usuario_atual["id"], itens)
        if sucesso:
            # Se der certo, limpa o carrinho e atualiza a tela.
            self.carrinho = {}
            self.atualizar_painel_carrinho()
            self.carregar_catalogo_cliente()
            messagebox.showinfo("Compra finalizada", mensagem)
        else:
            messagebox.showerror("Compra", mensagem)

    def mostrar_pedidos_cliente(self):
        # Abre uma janela com o histórico de pedidos do cliente.
        janela = tk.Toplevel(self.root)
        janela.title("Meus pedidos")
        janela.geometry("760x460")
        janela.configure(bg=self.cores["bg_sec"])

        tk.Label(janela, text="Histórico de pedidos", bg=self.cores["bg_sec"], fg="white", font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=20, pady=(20, 6))
        tk.Label(janela, text="Confira as compras feitas nesta conta.", bg=self.cores["bg_sec"], fg=self.cores["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=20)

        caixa = tk.Frame(janela, bg="white", padx=16, pady=16)
        caixa.pack(fill="both", expand=True, padx=20, pady=20)

        pedidos = self.db.pedidos_cliente(self.usuario_atual["id"])

        # Exibe uma mensagem se o cliente ainda não tiver pedidos.
        if not pedidos:
            tk.Label(caixa, text="Você ainda não realizou nenhuma compra.", bg="white", fg="#64748b", font=("Segoe UI", 12)).pack(anchor="w")
            return

        # Exibe o cabeçalho do pedido e os itens comprados.
        for pedido in pedidos:
            bloco = tk.Frame(caixa, bg="#f8fafc", padx=14, pady=14, highlightthickness=1, highlightbackground="#e2e8f0")
            bloco.pack(fill="x", pady=6)

            tk.Label(bloco, text=f"Pedido #{pedido['id']}", bg="#f8fafc", fg="#0f172a", font=("Segoe UI", 13, "bold")).pack(anchor="w")
            tk.Label(bloco, text=f"Data: {pedido['criado_em']}  •  Status: {pedido['status']}  •  Total: R$ {pedido['total']:.2f}", bg="#f8fafc", fg="#475569", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

            itens = self.db.itens_pedido(pedido["id"])
            for item in itens:
                tk.Label(
                    bloco,
                    text=f"- {item['nome_produto']} | {item['quantidade']}x | R$ {item['subtotal']:.2f}",
                    bg="#f8fafc",
                    fg="#334155",
                    font=("Segoe UI", 10),
                ).pack(anchor="w", pady=(6, 0))

    def ao_fechar(self):
        # Fecha o banco antes de encerrar a aplicação.
        self.db.fechar()
        self.root.destroy()


# Início da aplicação.
if __name__ == "__main__":
    root = tk.Tk()
    app = MercadoApp(root)
    root.mainloop()
