CREATE TABLE Nodos (
    id_nodo INT PRIMARY KEY,
    tipo VARCHAR(50), 
    propiedades JSON 
);

CREATE TABLE Aristas (
    id_origen INT,
    id_destino INT,
    tipo_relacion VARCHAR(50), 
    peso FLOAT, 
    FOREIGN KEY (id_origen) REFERENCES Nodos(id_nodo),
    FOREIGN KEY (id_destino) REFERENCES Nodos(id_nodo)
);