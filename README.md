# 🛒 Sistema de Mercado

Sistema desenvolvido para gerenciar as principais operações de um mercado, como cadastro de usuários, controle de produtos, estoque e realização de pedidos. O projeto foi criado em Python com interface gráfica, permitindo que diferentes tipos de usuários utilizem o sistema de acordo com seu perfil. 

---

## 📌 O que o sistema faz

O **Sistema de Mercado** permite controlar e organizar o funcionamento de um mercado em um único lugar. Ele possui login de usuários, cadastro de clientes, gerenciamento de produtos e controle de pedidos. O sistema também faz o controle de estoque automaticamente, diminuindo a quantidade disponível sempre que uma compra é finalizada. 

Além disso, o projeto possui diferentes perfis de acesso, como **dono**, **funcionário** e **cliente**. Cada perfil possui uma jornada diferente dentro do sistema. O dono e o funcionário acessam a área administrativa, enquanto o cliente entra na área de compras para visualizar produtos, adicionar itens ao carrinho e finalizar pedidos. 

---

## ⚙️ Como o projeto foi feito

O projeto foi desenvolvido em **Python**, utilizando uma estrutura organizada em classes para separar as responsabilidades do sistema. Uma parte do código é responsável pela comunicação com o banco de dados, criando as tabelas e executando operações como cadastro, consulta, atualização e exclusão de registros. Outra parte do código cuida da interface gráfica e da navegação entre as telas do sistema.

A lógica do sistema foi construída para simular o funcionamento real de um mercado. Quando o usuário faz login, o sistema identifica o seu perfil e direciona automaticamente para a tela correta. No caso do cliente, ele pode navegar pelo catálogo, adicionar produtos ao carrinho e finalizar o pedido. Já no caso do administrador e do funcionário, eles podem cadastrar produtos, atualizar estoques e visualizar os pedidos realizados.

As senhas dos usuários são protegidas com criptografia hash, garantindo mais segurança no armazenamento dos dados. O sistema também registra informações importantes, como produtos, pedidos, usuários e itens comprados, tudo salvo em banco de dados local.
---

## 💻 Tecnologias usadas

### Linguagem principal
- **Python** 

### Bibliotecas e recursos
- **Tkinter** → usada para construir a interface gráfica do sistema  
- **ttk** → usada para estilizar componentes visuais da interface  
- **SQLite3** → usado para armazenar os dados do sistema em banco local  
- **hashlib** → usado para criptografar as senhas com SHA-256  
- **datetime** → usado para registrar data e horário dos pedidos 

---

## 👥 Perfis de usuário

O sistema possui três tipos principais de usuários:

- **Dono**
- **Funcionário**
- **Cliente** 

Cada um deles possui uma experiência diferente dentro do sistema.

---

## 🔄 Jornada do usuário

### 1. Tela inicial
Ao abrir o sistema, o usuário encontra a **tela de login**. Nessa tela, ele pode entrar com uma conta já existente ou, se for cliente, realizar um novo cadastro.

### 2. Login
Depois de informar usuário e senha, o sistema verifica os dados no banco e identifica o perfil da pessoa que entrou. Com base nisso, ele redireciona para a área correta.

### 3. Jornada do dono
Se o usuário for o **dono**, ele entra no **painel administrativo**. Nessa tela, ele consegue:
- visualizar indicadores do mercado;
- cadastrar produtos;
- editar produtos;
- remover produtos;
- acompanhar pedidos;
- consultar faturamento e estoque. 

### 4. Jornada do funcionário
Se o usuário for **funcionário**, ele também entra na área administrativa. Sua jornada é parecida com a do dono, pois ele pode:
- acessar os produtos cadastrados;
- atualizar informações dos produtos;
- acompanhar pedidos;
- ajudar no controle de estoque. 

### 5. Jornada do cliente
Se o usuário for **cliente**, ele entra na **tela de catálogo de produtos**. A partir daí, sua jornada é a seguinte:

- faz login no sistema;
- acessa a tela de produtos;
- pesquisa ou filtra produtos por categoria;
- escolhe a quantidade desejada;
- adiciona produtos ao carrinho;
- visualiza o carrinho de compras;
- finaliza o pedido;
- consulta o histórico de pedidos.

### 6. Finalização do pedido
Quando o cliente conclui a compra, o sistema:
- registra o pedido no banco de dados;
- salva os itens comprados;
- calcula o valor total;
- atualiza o estoque automaticamente. 
