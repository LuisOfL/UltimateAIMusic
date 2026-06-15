CREATE TABLE cancion (

    id_cancion SERIAL, 
    
    duracion INT NOT NULL, 
    idioma VARCHAR(10) NOT NULL, 
    tema VARCHAR(100) NOT NULL, 
    genero VARCHAR(100) NOT NULL,
    id_autor VARCHAR(255) NOT NULL,

    CONSTRAINT pk_cancion PRIMARY KEY (id_cancion)
);


CREATE INDEX idx_cancion_autor ON cancion(id_autor);
CREATE INDEX idx_cancion_tema ON cancion(tema);