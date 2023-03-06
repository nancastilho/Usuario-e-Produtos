import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO produtos (produto, descricao, preco, estoqueloja, departamentos, anexos) VALUES (?, ?, ?, ?, ?, ?)",
            ('teste', 'teste',15,'5', "Esportivo", "teste.jpg")
            )

cur.execute("INSERT INTO setores (setor, vf) VALUES (?,?)",
            ('Esportivo', 'v')
            )


connection.commit()
connection.close()
